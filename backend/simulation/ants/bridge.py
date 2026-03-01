"""Army ant bridge formation simulation -- Module 2.

Models the physical bridge formation mechanism documented in:
  McCreery et al. (2022, Nature Communications) -- accumulator model,
    join/leave rules, hysteresis confirmation.
  Reid et al. (2015, PNAS) -- cost-benefit trade-off, equilibrium density
    0.51 ants/mm scaling parameter.

Environment
-----------
  Narrow corridor: corridor_width (default 3) rows x corridor_length cols.
  Nest at col=0, food at col=corridor_length-1.
  Gap: a horizontal band of cells [gap_start, gap_end] across all rows.

  Ants can traverse a gap directly (without a bridge) if gap_size <=
  min_jump_size (default 3), representing body-length-limited gap-crossing.
  Larger gaps require a bridge of LOCKED ants.

State machine
-------------
  WALKING (0): ant moves horizontally toward target (food or nest)
  LOCKED  (1): ant frozen in bridge position; enables adjacent gap traversal
  LEAVING (2): transitioning out of bridge -- becomes WALKING on next step

Join rule (WALKING -> LOCKED)
-----------------------------
  An ant at a bridge-eligible position (col in gap cells) that:
    (a) failed to move this step (blocked by impassable gap), AND
    (b) has transit count >= join_threshold in the last traffic_window steps,
    AND (c) no other LOCKED ant occupies its cell (one LOCKED ant per cell)
  -> LOCK at current position.
  Transit = another WALKING ant arriving at this ant's cell in a step.
  (Tactile pressure trigger: McCreery et al.)

Leave rule (LOCKED -> LEAVING)
------------------------------
  A LOCKED ant that receives ZERO traffic (no ants arriving at its cell)
  for leave_patience consecutive steps -> LEAVING -> WALKING (next step).
  (Slackness/tension signal: traffic = "being used"; no traffic = idle/slack.)

  The traffic-based leave rule is used in place of a population-count threshold
  because it cleanly operationalizes the biological slackness signal:
  - When ants walk over/through the locked ant, it stays (in use).
  - When traffic drops (bridge no longer needed, or gap becomes jumpable),
    the locked ant eventually leaves.
  This produces hysteresis: the bridge persists during ramp-down because
  traffic flows through it; dissolution only occurs when the gap shrinks
  below min_jump_size and ants bypass the bridge entirely.

Gap traversability
------------------
  If gap_size <= min_jump_size: all gap cells are directly traversable.
  Otherwise: gap cell (r, c) is traversable if a LOCKED ant is at (r, c)
    OR at the adjacent cell in the direction of travel:
      outbound (right):  LOCKED ant at (r, c-1) or (r, c)
      return   (left):   LOCKED ant at (r, c+1) or (r, c)
  Bridges grow one cell at a time as ants lock into position.

Hysteresis mechanism
--------------------
  Formation: ants block at gap edge only when gap > min_jump_size. The
    smallest blocking gap forms the bridge (formation_gap = min_jump_size + 1
    in the absence of other constraints).
  Dissolution: the bridge persists during ramp-down as long as ants use it.
    When gap_size decreases to <= min_jump_size, ants bypass the bridge;
    traffic drops to zero; locked ants leave after leave_patience steps.
    dissolution_gap = min_jump_size (or slightly below depending on dynamics).
  Hysteresis confirmed when dissolution_gap < formation_gap.

Metrics
-------
  bridge_size:        LOCKED ant count per step
  formation_gap:      smallest gap_size (during ramp-up) where mean bridge
                      size >= n_equilibrium during hold period
  dissolution_gap:    smallest gap_size (during ramp-down) where bridge
                      fully dissolves (mean bridge_size == 0)
  hysteresis_detected: dissolution_gap < formation_gap
  hysteresis_magnitude: formation_gap - dissolution_gap
  throughput:         round trips completed per step (nest deliveries)

SCI does not apply to Module 2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

WALKING = 0
LOCKED  = 1
LEAVING = 2


# -- Configuration -------------------------------------------------------------

@dataclass
class BridgeConfig:
    """All parameters for one bridge simulation run."""
    corridor_length: int   = 50
    corridor_width:  int   = 3
    # Ramp protocol (Experiment B)
    gap_min:         int   = 1
    gap_max:         int   = 30
    hold_steps:      int   = 500     # steps held at each gap size
    # Gap traversability
    min_jump_size:   int   = 3       # gaps <= this are directly traversable
    # Join rule
    join_threshold:  int   = 1       # transits in window to trigger lock
    traffic_window:  int   = 5       # rolling window for transit counts
    # Leave rule
    reid_coefficient: float = 0.51   # n_equilibrium = round(reid_coeff * gap_size)
    leave_patience:  int   = 5       # consecutive zero-traffic steps to leave
    # Colony
    n_ants:          int   = 100
    seed:            int   = 0
    output_dir:      str   = ""


# -- Bridge simulation ---------------------------------------------------------

class BridgeSimulation:

    def __init__(self, config: BridgeConfig, gap_size: int) -> None:
        self.cfg      = config
        self._rng     = np.random.default_rng(config.seed)
        self.gap_size = gap_size
        self._update_gap()

        H = config.corridor_width
        L = config.corridor_length
        N = config.n_ants

        # Ants: distribute randomly in nest half of corridor (left of gap)
        rows = self._rng.integers(0, H, size=N)
        max_start_col = max(0, self.gap_start - 1)
        cols = self._rng.integers(0, max_start_col + 1, size=N)
        self.positions   = np.column_stack([rows, cols]).astype(np.int32)
        self.modes       = np.zeros(N, dtype=np.int32)   # 0=outbound, 1=return
        self.states      = np.zeros(N, dtype=np.int32)   # WALKING

        # Traffic tracking: rolling circular buffer of per-step transit counts
        self._traffic_buf = np.zeros((N, config.traffic_window), dtype=np.int32)
        self._traffic_sum = np.zeros(N, dtype=np.int32)

        # Leave streak: consecutive steps with zero traffic (for LOCKED ants)
        self._leave_streak = np.zeros(N, dtype=np.int32)

        # Metrics
        self.bridge_size_history: list[int]   = []
        self.throughput_count:    int         = 0

        # Ramp results (populated by run_ramp)
        self.formation_gap:       Optional[int]  = None
        self.dissolution_gap:     Optional[int]  = None
        self.hysteresis_detected: Optional[bool] = None
        self.bridge_size_up:   dict[int, float]  = {}
        self.bridge_size_down: dict[int, float]  = {}

    # -- Gap geometry ----------------------------------------------------------

    def _update_gap(self) -> None:
        """Recompute gap_start/gap_end from current gap_size."""
        gc = self.cfg.corridor_length // 2
        if self.gap_size == 0:
            self.gap_start = gc
            self.gap_end   = gc - 1     # gap_end < gap_start means no gap cells
        else:
            self.gap_start = gc - self.gap_size // 2
            self.gap_end   = self.gap_start + self.gap_size - 1

    def _is_gap_cell(self, c: int) -> bool:
        if self.gap_size == 0:
            return False
        return self.gap_start <= c <= self.gap_end

    def _n_equilibrium(self) -> int:
        return max(1, round(self.cfg.reid_coefficient * self.gap_size))

    def _gap_requires_bridge(self) -> bool:
        """True if ants cannot cross the gap without a bridge."""
        return self.gap_size > self.cfg.min_jump_size

    def _is_bridge_eligible(self, c: int) -> bool:
        """Bridge-eligible: gap cells PLUS immediate boundary cells, only when
        gap requires bridge.  The boundary cells (gap_start-1, gap_end+1) are
        the anchor points where the bridge begins forming -- ants lock there
        first, making the first gap cell traversable."""
        if not self._gap_requires_bridge():
            return False
        return self.gap_start - 1 <= c <= self.gap_end + 1

    # -- Traversability --------------------------------------------------------

    def _build_locked_set(self) -> set[tuple[int, int]]:
        return {
            (int(self.positions[i, 0]), int(self.positions[i, 1]))
            for i in range(self.cfg.n_ants)
            if self.states[i] == LOCKED
        }

    def _is_traversable(self, r: int, c: int, direction: int,
                        locked_set: set[tuple[int, int]]) -> bool:
        """Can an ant moving in direction (+1=right, -1=left) enter cell (r,c)?"""
        if not self._is_gap_cell(c):
            return True
        # Small gap: directly walkable without a bridge
        if not self._gap_requires_bridge():
            return True
        # Already has a locked ant -- traversable for either direction
        if (r, c) in locked_set:
            return True
        # Chain-rule: locked ant at the preceding cell in direction of travel
        preceding_c = c - direction   # cell BEHIND (r,c) in the direction of travel
        return (r, preceding_c) in locked_set

    # -- Single timestep -------------------------------------------------------

    def step(self, t: int) -> None:
        H  = self.cfg.corridor_width
        L  = self.cfg.corridor_length
        tw = self.cfg.traffic_window
        n_eq = self._n_equilibrium()

        locked_set = self._build_locked_set()

        # --- Movement (WALKING ants only) ---
        new_positions = self.positions.copy()
        transit_count: dict[tuple[int, int], int] = {}   # (r,c) -> arrivals this step
        stayed = np.ones(self.cfg.n_ants, dtype=bool)    # True = ant did NOT move this step

        for i in range(self.cfg.n_ants):
            if self.states[i] != WALKING:
                stayed[i] = False  # LOCKED/LEAVING ants are not "waiting"
                continue

            r, c       = int(self.positions[i, 0]), int(self.positions[i, 1])
            direction  = 1 if self.modes[i] == 0 else -1
            new_c      = c + direction

            if new_c < 0 or new_c >= L:
                stayed[i] = False   # at corridor boundary, not gap-blocked
                continue

            if not self._is_traversable(r, new_c, direction, locked_set):
                # Blocked by gap -- ant stays; stayed[i] remains True
                continue

            # Successfully moved
            new_positions[i, 1] = new_c
            stayed[i] = False
            key = (r, new_c)
            transit_count[key] = transit_count.get(key, 0) + 1

        # --- Update traffic rolling window ---
        slot = t % tw
        self._traffic_sum -= self._traffic_buf[:, slot]
        for i in range(self.cfg.n_ants):
            r_new = int(new_positions[i, 0])
            c_new = int(new_positions[i, 1])
            self._traffic_buf[i, slot] = transit_count.get((r_new, c_new), 0)
        self._traffic_sum += self._traffic_buf[:, slot]

        # Apply movements
        self.positions = new_positions

        # --- Arrival checks and mode switching ---
        for i in range(self.cfg.n_ants):
            if self.states[i] != WALKING:
                continue
            c = int(self.positions[i, 1])
            if self.modes[i] == 0 and c == L - 1:   # reached food
                self.modes[i] = 1
            elif self.modes[i] == 1 and c == 0:      # reached nest
                self.modes[i] = 0
                self.throughput_count += 1

        # --- State transitions ---
        # LEAVING -> WALKING (always, one step)
        leaving_mask = (self.states == LEAVING)
        self.states[leaving_mask] = WALKING
        self._leave_streak[leaving_mask] = 0

        # Rebuild locked set after positions applied
        locked_set_new = self._build_locked_set()

        for i in range(self.cfg.n_ants):
            r, c  = int(self.positions[i, 0]), int(self.positions[i, 1])
            state = int(self.states[i])

            if state == WALKING:
                # Join rule: ant must be BLOCKED (stayed in place due to gap),
                # at a bridge-eligible position, with sufficient incoming traffic,
                # AND no other LOCKED ant is already at this cell (one per cell).
                if stayed[i] and self._is_bridge_eligible(c):
                    if self._traffic_sum[i] >= self.cfg.join_threshold:
                        if (r, c) not in locked_set_new:
                            self.states[i] = LOCKED
                            locked_set_new.add((r, c))

            elif state == LOCKED:
                # Force release if gap changed and ant is no longer bridge-eligible
                if not self._is_bridge_eligible(c):
                    self.states[i] = LEAVING
                    self._leave_streak[i] = 0
                    continue

                # Leave rule: zero traffic for leave_patience consecutive steps.
                # A locked ant with no traffic is idle -- the bridge is not needed
                # at this position. Matches the biological slackness signal.
                if self._traffic_sum[i] == 0:
                    self._leave_streak[i] += 1
                    if self._leave_streak[i] >= self.cfg.leave_patience:
                        self.states[i] = LEAVING
                        self._leave_streak[i] = 0
                else:
                    self._leave_streak[i] = 0

        # Record bridge size
        bridge_size = int((self.states == LOCKED).sum())
        self.bridge_size_history.append(bridge_size)

    # -- Run modes -------------------------------------------------------------

    def run(self, n_steps: int) -> None:
        """Run for n_steps at current gap_size."""
        for t in range(n_steps):
            self.step(t)

    def set_gap_size(self, new_gap_size: int) -> None:
        """Change gap size; release LOCKED ants no longer in bridge region."""
        self.gap_size = new_gap_size
        self._update_gap()
        for i in range(self.cfg.n_ants):
            if self.states[i] == LOCKED:
                c = int(self.positions[i, 1])
                if not self._is_bridge_eligible(c):
                    self.states[i] = LEAVING
                    self._leave_streak[i] = 0

    def run_ramp(self) -> None:
        """
        Gap ramp experiment: increase gap_size from gap_min to gap_max, then
        decrease back to gap_min. Record bridge_size at each gap level.

        Warmup: hold_steps at gap_min before starting the ramp.
        Phase 1 (up): gap_min -> gap_max, hold_steps each.
        Phase 2 (down): gap_max -> gap_min, hold_steps each.

        formation_gap:   first gap (during up) where mean bridge_size >= n_equilibrium
        dissolution_gap: first gap (during down) where mean bridge_size == 0
        hysteresis:      dissolution_gap < formation_gap
        """
        cfg = self.cfg
        t   = 0

        # Warmup at gap_min
        self.set_gap_size(cfg.gap_min)
        for _ in range(cfg.hold_steps):
            self.step(t)
            t += 1

        # Phase 1: ramp UP
        form_found = False
        for gap_s in range(cfg.gap_min, cfg.gap_max + 1):
            self.set_gap_size(gap_s)
            n_eq = max(1, round(cfg.reid_coefficient * gap_s))
            sizes = []
            for _ in range(cfg.hold_steps):
                self.step(t)
                t += 1
                sizes.append(self.bridge_size_history[-1])
            mean_s = sum(sizes) / len(sizes)
            self.bridge_size_up[gap_s] = round(mean_s, 2)
            if not form_found and mean_s >= n_eq:
                self.formation_gap = gap_s
                form_found = True

        # Phase 2: ramp DOWN
        diss_found = False
        for gap_s in range(cfg.gap_max, cfg.gap_min - 1, -1):
            self.set_gap_size(gap_s)
            sizes = []
            for _ in range(cfg.hold_steps):
                self.step(t)
                t += 1
                sizes.append(self.bridge_size_history[-1])
            mean_s = sum(sizes) / len(sizes)
            self.bridge_size_down[gap_s] = round(mean_s, 2)
            if not diss_found and mean_s == 0:
                diss_found = True
                self.dissolution_gap = gap_s

        if form_found and diss_found:
            self.hysteresis_detected = (self.dissolution_gap < self.formation_gap)
        else:
            self.hysteresis_detected = False

    # -- Aggregate metrics -----------------------------------------------------

    def throughput(self) -> float:
        total = len(self.bridge_size_history)
        return round(self.throughput_count / max(total, 1), 6)

    def mean_bridge_size(self) -> float:
        if not self.bridge_size_history:
            return 0.0
        return round(sum(self.bridge_size_history) / len(self.bridge_size_history), 2)

    # -- Manifest I/O ----------------------------------------------------------

    def write_manifest(self) -> None:
        if not self.cfg.output_dir:
            return
        out = Path(self.cfg.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        manifest = {
            "gap_size":              self.gap_size,
            "n_ants":                self.cfg.n_ants,
            "corridor_length":       self.cfg.corridor_length,
            "corridor_width":        self.cfg.corridor_width,
            "min_jump_size":         self.cfg.min_jump_size,
            "join_threshold":        self.cfg.join_threshold,
            "traffic_window":        self.cfg.traffic_window,
            "reid_coefficient":      self.cfg.reid_coefficient,
            "leave_patience":        self.cfg.leave_patience,
            "seed":                  self.cfg.seed,
            "n_steps":               len(self.bridge_size_history),
            "max_bridge_size":       max(self.bridge_size_history)
                                     if self.bridge_size_history else 0,
            "mean_bridge_size":      self.mean_bridge_size(),
            "final_bridge_size":     self.bridge_size_history[-1]
                                     if self.bridge_size_history else 0,
            "throughput":            self.throughput(),
            "throughput_count":      self.throughput_count,
            "formation_gap":         self.formation_gap,
            "dissolution_gap":       self.dissolution_gap,
            "hysteresis_detected":   self.hysteresis_detected,
            "hysteresis_magnitude":  (self.formation_gap - self.dissolution_gap)
                                     if self.formation_gap is not None
                                     and self.dissolution_gap is not None
                                     else None,
            "bridge_size_up":        self.bridge_size_up,
            "bridge_size_down":      self.bridge_size_down,
        }
        with open(out / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
