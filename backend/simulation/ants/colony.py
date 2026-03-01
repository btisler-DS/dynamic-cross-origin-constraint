"""Stigmergic ant colony simulation.

Models a 2D foraging grid where ants coordinate via pheromone gradients without
any learning or internal representation. This implements the implicit-Delta case
for testing whether Delta-Variable Theory structural signatures (phase-like formation,
hysteresis, non-monotonic coupling window) appear in non-representational systems.

Pheromone layers — cross-layer following (standard ACO)
-------------------------------------------------------
  Layer 0 — outbound pheromone: deposited by outbound ants (mode=0)
             followed by RETURN ants to guide them back to nest
  Layer 1 — return pheromone:   deposited by return ants (mode=1)
             followed by OUTBOUND ants to guide them toward food

Cross-layer rationale: outbound ants deposit a trace of where they
explored (layer 0), which return ants use to find their way home.
Return ants deposit a trace of successful food→nest paths (layer 1),
which future outbound ants use to find food faster. This mirrors
real Dorigo ACO and avoids positive-feedback oscillation from
same-layer deposit+follow.

Parallel updates: all deposits are buffered and applied after all
ants have moved each step. This prevents within-step ordering artefacts
(first ant deposits, later ants immediately follow that single deposit).

Movement rule — strictly-forward gradient
-----------------------------------------
  - Compute curr_dist = Manhattan distance from current cell to target.
  - Forward neighbors: those with distance-to-target STRICTLY LESS than curr_dist.
  - If max pheromone on followed layer among forward neighbors >= theta_decision:
      move to highest-pheromone forward neighbor (gradient following).
  - Otherwise: Delta-event; move probabilistically weighted by 1/(dist+1).
  Lateral moves (same distance) are excluded from gradient following to prevent
  cross-trail oscillation.

Stigmergic Coupling Index (SCI)
--------------------------------
  SCI = P(gradient crosses theta_decision within tau steps | gradient below
          theta_decision at t)

  Delta-event: ant at position (r,c) where max pheromone in strictly-forward
               Moore neighborhood on the followed layer is below theta_decision.
  Closure: within tau steps, that max crosses theta_decision (because a
           forager reinforced pheromone in the neighborhood).

See ants-implicit-delta.md for theoretical framing.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

# Moore neighborhood offsets (8 directions)
_OFFSETS = [(-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1)]


# ── Configuration ─────────────────────────────────────────────────────────────

@dataclass
class AntConfig:
    """All parameters for one colony simulation run."""
    # Grid
    grid_size:       int   = 50
    # Colony
    n_ants:          int   = 100
    n_steps:         int   = 2000
    # Pheromone dynamics — the primary cost levers
    epsilon:         float = 0.01    # evaporation rate per step
    delta:           float = 0.10    # deposition rate per step per ant
    # Decision threshold (preregistered as 25th percentile of pilot gradient distribution)
    theta_decision:  float = 0.10
    # SCI closure window (preregistered as tau=20)
    tau:             int   = 20
    # Crystallization: entropy below threshold for this many consecutive steps
    entropy_streak:  int   = 5
    # Hysteresis sweep parameters (Exp B only)
    hys_eps_start:   float = 0.005   # lowest epsilon (stable trail expected)
    hys_eps_end:     float = 0.060   # highest epsilon (dissolution expected)
    hys_eps_step:    float = 0.002   # step size
    hys_steps_level: int   = 500     # steps held at each epsilon level
    hys_dissolved_k: int   = 10      # consecutive steps above threshold = dissolved
    # Misc
    seed:            int   = 0
    output_dir:      str   = ""


# ── SCI event tracking ────────────────────────────────────────────────────────

class _SCIEvent:
    __slots__ = ("r", "c", "t_start", "layer", "resolved")

    def __init__(self, r: int, c: int, t_start: int, layer: int) -> None:
        self.r       = r
        self.c       = c
        self.t_start = t_start
        self.layer   = layer
        self.resolved = False


# ── Colony simulation ─────────────────────────────────────────────────────────

class ColonySimulation:

    def __init__(self, config: AntConfig) -> None:
        self.cfg  = config
        self._rng = np.random.default_rng(config.seed)

        H = W = config.grid_size
        self.H, self.W = H, W
        self.nest = np.array([0,     0    ], dtype=np.int32)
        self.food = np.array([H - 1, W - 1], dtype=np.int32)

        # Entropy threshold: 60% of log2(H*W)  [matches MARL 0.95/1.585 ≈ 60% logic]
        self._entropy_max       = math.log2(H * W)
        self._entropy_threshold = 0.60 * self._entropy_max

        # Pheromone matrix: (2, H, W)
        #   [0] = outbound pheromone (deposited by outbound ants, followed by return ants)
        #   [1] = return pheromone   (deposited by return ants,   followed by outbound ants)
        self.pheromone = np.zeros((2, H, W), dtype=np.float64)

        # Ants: all start at nest, outbound mode
        self.positions = np.zeros((config.n_ants, 2), dtype=np.int32)
        self.modes     = np.zeros(config.n_ants,      dtype=np.int32)

        # SCI
        self._sci_pending:  list[_SCIEvent] = []
        self._sci_resolved: int = 0
        self._sci_total:    int = 0

        # Metrics history
        self.entropy_history:    list[float] = []
        self._crys_streak:       int   = 0
        self._entropy_seen_high: bool  = False   # must rise above threshold first
        self.crystallization_step: Optional[int] = None
        self.food_delivered:     int   = 0

        # Hysteresis results (populated by run_hysteresis)
        self.formation_threshold:   Optional[float] = None
        self.dissolution_threshold: Optional[float] = None
        self.hysteresis_detected:   Optional[bool]  = None

        # Snapshot storage (for smoke test)
        self._snapshot_steps: set[int]            = set()
        self.snapshots:       dict[int, np.ndarray] = {}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        return [(r + dr, c + dc)
                for dr, dc in _OFFSETS
                if 0 <= r + dr < self.H and 0 <= c + dc < self.W]

    def _max_fwd_phero(self, r: int, c: int, layer: int,
                       target: np.ndarray) -> float:
        """Max pheromone on strictly-forward neighbors (dist < curr_dist)."""
        curr_dist = abs(r - target[0]) + abs(c - target[1])
        best = 0.0
        for nr, nc in self._neighbors(r, c):
            if abs(nr - target[0]) + abs(nc - target[1]) < curr_dist:
                v = float(self.pheromone[layer, nr, nc])
                if v > best:
                    best = v
        return best

    def _path_entropy(self) -> float:
        """Shannon entropy (log2) of combined pheromone distribution."""
        combined = self.pheromone[0] + self.pheromone[1]
        total = combined.sum()
        if total < 1e-12:
            return self._entropy_max   # no pheromone = maximum wandering
        p = combined.ravel() / total
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))

    def _dist_weights(self,
                      neighbors: list[tuple[int, int]],
                      target: np.ndarray) -> np.ndarray:
        w = np.array([1.0 / (abs(nr - target[0]) + abs(nc - target[1]) + 1)
                      for nr, nc in neighbors], dtype=np.float64)
        return w / w.sum()

    # ── Per-ant movement ──────────────────────────────────────────────────────

    def _move_ant(self, i: int, t: int, _deposits: np.ndarray) -> None:
        r, c  = int(self.positions[i, 0]), int(self.positions[i, 1])
        mode  = int(self.modes[i])

        # Cross-layer: outbound ants follow return pheromone (layer 1);
        #              return ants follow outbound pheromone (layer 0).
        follow_layer  = 1 - mode   # 0->1 (outbound follows return), 1->0 (return follows outbound)
        deposit_layer = mode        # 0 (outbound deposits on layer 0), 1 (return on layer 1)
        target = self.food if mode == 0 else self.nest

        nbrs = self._neighbors(r, c)
        if not nbrs:
            return

        curr_dist = abs(r - target[0]) + abs(c - target[1])

        # Strictly-forward neighbors (dist < curr_dist) and their pheromone
        fwd_phero = np.array([
            float(self.pheromone[follow_layer, nr, nc])
            if abs(nr - target[0]) + abs(nc - target[1]) < curr_dist
            else 0.0
            for nr, nc in nbrs
        ])
        max_fwd = float(fwd_phero.max())

        if max_fwd > 0 and max_fwd >= self.cfg.theta_decision:
            # Follow gradient: move to highest-pheromone strictly-forward neighbor
            new_r, new_c = nbrs[int(np.argmax(fwd_phero))]
        else:
            # Implicit Delta-event: no usable forward gradient
            self._sci_pending.append(_SCIEvent(r=r, c=c, t_start=t, layer=follow_layer))
            self._sci_total += 1
            # Move probabilistically by inverse distance to target (all neighbors eligible)
            weights = self._dist_weights(nbrs, target)
            idx = int(self._rng.choice(len(nbrs), p=weights))
            new_r, new_c = nbrs[idx]

        self.positions[i] = [new_r, new_c]

        # Buffer pheromone deposit (applied after ALL ants have moved — parallel update).
        # Parallel updates prevent within-step ordering artefacts where early ants'
        # deposits immediately attract all later ants within the same timestep.
        _deposits[deposit_layer, new_r, new_c] += self.cfg.delta

        # Check arrival at food or nest
        if mode == 0 and new_r == int(self.food[0]) and new_c == int(self.food[1]):
            self.modes[i] = 1                      # switch to return
        elif mode == 1 and new_r == int(self.nest[0]) and new_c == int(self.nest[1]):
            self.modes[i] = 0                      # switch to outbound
            self.food_delivered += 1

    # ── SCI resolution ────────────────────────────────────────────────────────

    def _resolve_sci(self, t: int) -> None:
        still_pending: list[_SCIEvent] = []
        for ev in self._sci_pending:
            age = t - ev.t_start
            if age > self.cfg.tau:
                pass  # expired unresolved
            elif self._max_fwd_phero(ev.r, ev.c, ev.layer,
                                     self.food if ev.layer == 1 else self.nest) \
                    >= self.cfg.theta_decision:
                self._sci_resolved += 1
                # don't keep in pending
            else:
                still_pending.append(ev)
        self._sci_pending = still_pending

    # ── Single timestep ───────────────────────────────────────────────────────

    def step(self, t: int) -> None:
        # Parallel deposit buffer: all ants decide and move based on pheromone
        # from the PREVIOUS step. Deposits are collected here and applied after
        # all ants have moved.
        _deposits = np.zeros((2, self.H, self.W), dtype=np.float64)

        for i in range(self.cfg.n_ants):
            self._move_ant(i, t, _deposits)

        # Apply buffered deposits, then evaporate
        self.pheromone += _deposits
        self.pheromone *= (1.0 - self.cfg.epsilon)
        np.clip(self.pheromone, 0.0, None, out=self.pheromone)

        self._resolve_sci(t)

        # Record entropy and check crystallization
        h = self._path_entropy()
        self.entropy_history.append(h)

        if self.crystallization_step is None:
            if h >= self._entropy_threshold:
                # Entropy is high — exploration phase, reset streak
                self._entropy_seen_high = True
                self._crys_streak = 0
            elif self._entropy_seen_high:
                # Entropy dropped below threshold after exploration — count streak
                self._crys_streak += 1
                if self._crys_streak >= self.cfg.entropy_streak:
                    self.crystallization_step = t - self.cfg.entropy_streak + 1
            # If entropy never rose above threshold yet, skip (initial warm-up phase)

        # Snapshots (combined pheromone — both layers — for visual trail detection)
        if t in self._snapshot_steps:
            self.snapshots[t] = (self.pheromone[0] + self.pheromone[1]).copy()

    # ── Run modes ─────────────────────────────────────────────────────────────

    def run(self, snapshot_steps: Optional[list[int]] = None) -> None:
        """Standard run: n_steps from current state."""
        if snapshot_steps:
            self._snapshot_steps = set(snapshot_steps)
        for t in range(self.cfg.n_steps):
            self.step(t)

    def run_hysteresis(self) -> None:
        """
        Exp B: ramp epsilon up until trail dissolves, then down until it reforms.
        Populates self.dissolution_threshold and self.formation_threshold.

        Protocol:
          1. Warm up at hys_eps_start for n_steps to establish trail
          2. Increase epsilon in hys_eps_step increments, hys_steps_level steps each
             -> record dissolution_threshold (first epsilon where entropy stays above
               threshold for hys_dissolved_k consecutive steps)
          3. From dissolved state, decrease epsilon back down
             -> record formation_threshold (first epsilon where entropy stays below
               threshold for entropy_streak consecutive steps)
        """
        cfg = self.cfg

        # Phase 0: warm up at stable epsilon to establish trail
        self.cfg = AntConfig(**{**cfg.__dict__, "epsilon": cfg.hys_eps_start,
                                "n_steps": cfg.n_steps})
        for t in range(cfg.n_steps):
            self.step(t)

        # Phase 1: ramp epsilon UP
        eps_values = np.arange(cfg.hys_eps_start, cfg.hys_eps_end + cfg.hys_eps_step / 2,
                               cfg.hys_eps_step)
        diss_streak = 0
        diss_found  = False
        t_offset    = cfg.n_steps

        for eps in eps_values:
            self.cfg.epsilon = float(eps)
            for k in range(cfg.hys_steps_level):
                self.step(t_offset)
                t_offset += 1
                h = self.entropy_history[-1]
                if h > self._entropy_threshold:
                    diss_streak += 1
                    if diss_streak >= cfg.hys_dissolved_k:
                        self.dissolution_threshold = float(eps)
                        diss_found = True
                        break
                else:
                    diss_streak = 0
            if diss_found:
                break

        # Phase 2: ramp epsilon DOWN from dissolution point
        if diss_found:
            eps_down = np.arange(self.dissolution_threshold,
                                 cfg.hys_eps_start - cfg.hys_eps_step / 2,
                                 -cfg.hys_eps_step)
            form_streak = 0
            form_found  = False

            for eps in eps_down:
                self.cfg.epsilon = float(eps)
                for k in range(cfg.hys_steps_level):
                    self.step(t_offset)
                    t_offset += 1
                    h = self.entropy_history[-1]
                    if h < self._entropy_threshold:
                        form_streak += 1
                        if form_streak >= cfg.entropy_streak:
                            self.formation_threshold = float(eps)
                            form_found = True
                            break
                    else:
                        form_streak = 0
                if form_found:
                    break

            if diss_found and form_found:
                # Hysteresis: dissolution occurs at higher epsilon than formation
                self.hysteresis_detected = (
                    self.dissolution_threshold > self.formation_threshold + cfg.hys_eps_step / 2
                )
            else:
                self.hysteresis_detected = False
        else:
            self.hysteresis_detected = False

        self.cfg.epsilon = cfg.epsilon   # restore

    # ── Aggregate metrics ─────────────────────────────────────────────────────

    def sci(self) -> Optional[float]:
        if self._sci_total == 0:
            return None
        return round(self._sci_resolved / self._sci_total, 4)

    def throughput(self) -> float:
        total_steps = len(self.entropy_history)
        return round(self.food_delivered / max(total_steps, 1), 6)

    def mean_dominant_gradient(self) -> float:
        """Mean combined pheromone on cells above 75th percentile of combined field."""
        phero = self.pheromone[0] + self.pheromone[1]
        nonzero = phero[phero > 0]
        if len(nonzero) == 0:
            return 0.0
        threshold = np.percentile(nonzero, 75)
        return float(phero[phero >= threshold].mean())

    # ── Manifest I/O ──────────────────────────────────────────────────────────

    def write_manifest(self) -> None:
        if not self.cfg.output_dir:
            return
        out = Path(self.cfg.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        manifest = {
            "epsilon":                self.cfg.epsilon,
            "delta":                  self.cfg.delta,
            "n_ants":                 self.cfg.n_ants,
            "n_steps":                len(self.entropy_history),
            "grid_size":              self.cfg.grid_size,
            "theta_decision":         self.cfg.theta_decision,
            "tau":                    self.cfg.tau,
            "seed":                   self.cfg.seed,
            "crystallization_step":   self.crystallization_step,
            "SCI":                    self.sci(),
            "sci_total_events":       self._sci_total,
            "sci_resolved_events":    self._sci_resolved,
            "throughput":             self.throughput(),
            "food_delivered":         self.food_delivered,
            "final_entropy":          round(self.entropy_history[-1], 4)
                                      if self.entropy_history else None,
            "mean_dominant_gradient": round(self.mean_dominant_gradient(), 4),
            "hysteresis_detected":    self.hysteresis_detected,
            "formation_threshold":    self.formation_threshold,
            "dissolution_threshold":  self.dissolution_threshold,
        }
        with open(out / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
