"""Two-phase engine for Experiment 2 — Hysteresis Sweep.

Tests P3: do crystallised interrogative protocols persist when query cost is
reduced below the formation threshold?

Phase 1  Protocol 1, query_cost=phase1_query_cost (baseline: 1.5×).
         Runs until crystallisation (H < 0.95 for 5 consecutive epochs)
         is detected, then continues for grace_epochs more to confirm stability.

Phase 2  All agent parameters frozen (no gradient updates).
         query_cost reduced to phase2_query_cost (below formation: 1.2×).
         Runs for phase2_epochs epochs.

Pass signature  H remains < 0.95 for ≥ 80% of phase 2 epochs → hysteresis confirmed.
Fail signature  H rises back above 0.95 within 20 epochs of cost reduction → falsifies P3.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from ..engine import SimulationConfig, SimulationEngine

# ── Constants ─────────────────────────────────────────────────────────────────

CRYSTALLIZATION_THRESHOLD = 0.95   # type_entropy must drop below this
CRYSTALLIZATION_STREAK    = 5      # consecutive epochs required
PASS_PERSISTENCE_RATE     = 0.80   # fraction of phase-2 epochs below threshold → pass


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class HysteresisConfig:
    seed: int = 0

    # Phase 1 — formation condition (preregistered baseline)
    phase1_query_cost:   float = 1.5
    phase1_respond_cost: float = 0.8

    # Phase 2 — below-formation condition (preregistered low_pressure)
    phase2_query_cost:   float = 1.2
    phase2_respond_cost: float = 0.9

    # Timing
    max_phase1_epochs:   int = 300   # ceiling; terminates early on crystallisation
    grace_epochs:        int = 10    # epochs after crystallisation before freeze
    phase2_epochs:       int = 100   # post-freeze observation window

    episodes_per_epoch:  int = 10
    output_dir:          str = "."


# ── Engine ────────────────────────────────────────────────────────────────────

class HysteresisEngine:
    """Orchestrates the two-phase hysteresis sweep for a single seed."""

    def __init__(self, config: HysteresisConfig) -> None:
        self.config = config
        self.crystallization_epoch: int | None = None
        self.freeze_epoch: int | None = None

        sim_config = SimulationConfig(
            seed=config.seed,
            num_epochs=config.max_phase1_epochs,
            episodes_per_epoch=config.episodes_per_epoch,
            protocol=1,
            declare_cost=1.0,
            query_cost=config.phase1_query_cost,
            respond_cost=config.phase1_respond_cost,
            output_dir=config.output_dir,
        )
        self.engine = SimulationEngine(config=sim_config)

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self) -> dict:
        """Run both phases. Returns manifest dict (also written to disk)."""
        phase1_metrics = self._run_phase1()

        if self.crystallization_epoch is None:
            return self._write_manifest(phase1_metrics, [], crystallized=False)

        # Freeze all agent parameters
        for agent in self.engine.agents:
            for param in agent.parameters():
                param.requires_grad_(False)

        # Disable optimizer step for phase 2
        self.engine.config.training_frozen = True

        # Reduce query cost below formation threshold
        self.engine.protocol.query_cost   = self.config.phase2_query_cost
        self.engine.protocol.respond_cost = self.config.phase2_respond_cost

        phase2_metrics = self._run_phase2(start_epoch=len(phase1_metrics))
        return self._write_manifest(phase1_metrics, phase2_metrics, crystallized=True)

    # ── Phase runners ─────────────────────────────────────────────────────────

    def _run_phase1(self) -> list[dict]:
        """Run epochs until crystallisation + grace period, then stop."""
        metrics: list[dict] = []
        streak_count = 0
        streak_start: int | None = None

        for epoch in range(self.config.max_phase1_epochs):
            m = self.engine._run_epoch(epoch)
            self.engine.epoch_metrics.append(m)
            metrics.append(m)

            # Inline crystallisation detection (mirrors engine._find_crystallization_epoch)
            inq = m.get("inquiry", {})
            te  = inq.get("type_entropy") if isinstance(inq, dict) else None

            if te is not None and te < CRYSTALLIZATION_THRESHOLD:
                if streak_count == 0:
                    streak_start = epoch
                streak_count += 1
                if streak_count >= CRYSTALLIZATION_STREAK and self.crystallization_epoch is None:
                    self.crystallization_epoch = streak_start
                    self.freeze_epoch = epoch + self.config.grace_epochs
            else:
                streak_count = 0
                streak_start = None

            if self.freeze_epoch is not None and epoch >= self.freeze_epoch:
                break

        return metrics

    def _run_phase2(self, start_epoch: int) -> list[dict]:
        """Run phase 2 with frozen agents and reduced query cost."""
        metrics: list[dict] = []
        for i in range(self.config.phase2_epochs):
            m = self.engine._run_epoch(start_epoch + i)
            metrics.append(m)
        return metrics

    # ── Manifest ──────────────────────────────────────────────────────────────

    def _write_manifest(
        self,
        phase1_metrics: list[dict],
        phase2_metrics: list[dict],
        crystallized: bool,
    ) -> dict:
        """Build and write hysteresis_manifest.json. Returns the dict."""
        phase2_entropy, phase2_qrc = [], []
        for m in phase2_metrics:
            inq = m.get("inquiry", {})
            if isinstance(inq, dict):
                te  = inq.get("type_entropy")
                qrc = inq.get("query_response_coupling")
                if te  is not None: phase2_entropy.append(round(te,  4))
                if qrc is not None: phase2_qrc.append(   round(qrc, 4))

        persisting = sum(1 for h in phase2_entropy if h < CRYSTALLIZATION_THRESHOLD)
        persistence_rate = persisting / len(phase2_entropy) if phase2_entropy else 0.0
        hysteresis_detected = persistence_rate >= PASS_PERSISTENCE_RATE if crystallized else None

        # Late phase-1 entropy for visual continuity in plots
        phase1_late_entropy = []
        for m in phase1_metrics[-50:]:
            inq = m.get("inquiry", {})
            if isinstance(inq, dict):
                te = inq.get("type_entropy")
                if te is not None:
                    phase1_late_entropy.append(round(te, 4))

        manifest = {
            "experiment": "hysteresis",
            "preregistered_prediction": "P3",
            "seed": self.config.seed,
            "phase1_query_cost":   self.config.phase1_query_cost,
            "phase1_respond_cost": self.config.phase1_respond_cost,
            "phase2_query_cost":   self.config.phase2_query_cost,
            "phase2_respond_cost": self.config.phase2_respond_cost,
            "grace_epochs":        self.config.grace_epochs,
            "crystallized":        crystallized,
            "crystallization_epoch":  self.crystallization_epoch,
            "freeze_epoch":           self.freeze_epoch,
            "phase1_epochs_run":      len(phase1_metrics),
            "phase2_epochs_run":      len(phase2_metrics),
            "hysteresis_detected":    hysteresis_detected,
            "persistence_rate":       round(persistence_rate, 4) if crystallized else None,
            "pass_threshold":         PASS_PERSISTENCE_RATE,
            "final_phase2_entropy":   phase2_entropy[-1] if phase2_entropy else None,
            "final_phase2_qrc":       phase2_qrc[-1]     if phase2_qrc     else None,
            "phase1_late_entropy":    phase1_late_entropy,
            "phase2_entropy_trajectory": phase2_entropy,
            "phase2_qrc_trajectory":     phase2_qrc,
        }

        os.makedirs(self.config.output_dir, exist_ok=True)
        path = os.path.join(self.config.output_dir, "hysteresis_manifest.json")
        with open(path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest
