"""Ant colony smoke test and pilot calibration.

Runs a single colony simulation and produces:
  1. Four-panel pheromone heatmap at steps 0, 500, 1000, 2000
     (confirms trails form and are spatially coherent, not edge-following)
  2. Console entropy timeseries and crystallization detection
  3. Pilot gradient calibration: records all gradient values seen at Δ-events
     to set theta_decision = 25th percentile (lock in preregistration)

Usage
-----
  python run_ant_smoke.py [--seed 0] [--delta 0.10] [--epsilon 0.01]
  python run_ant_smoke.py --calibrate [--pilot-steps 500]
  python run_ant_smoke.py --save-fig smoke_test.png
"""

from __future__ import annotations

import argparse
import math
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from simulation.ants.colony import AntConfig, ColonySimulation, _OFFSETS


# ── Pilot calibration: sample gradient distribution for theta_decision ────────

class _CalibratingColony(ColonySimulation):
    """ColonySimulation that records neighbor gradient values at Δ-events."""

    def __init__(self, config: AntConfig) -> None:
        super().__init__(config)
        self._gradient_samples: list[float] = []

    def _move_ant(self, i: int, t: int) -> None:
        r, c  = int(self.positions[i, 0]), int(self.positions[i, 1])
        mode  = int(self.modes[i])
        layer = mode
        target = self.food if mode == 0 else self.nest

        self.pheromone[layer, r, c] += self.cfg.delta

        nbrs    = self._neighbors(r, c)
        if not nbrs:
            return

        n_phero   = np.array([self.pheromone[layer, nr, nc] for nr, nc in nbrs])
        max_phero = float(n_phero.max())

        # Record ALL gradient values (not just below-threshold ones) for calibration
        self._gradient_samples.append(max_phero)

        if max_phero >= self.cfg.theta_decision:
            new_r, new_c = nbrs[int(np.argmax(n_phero))]
        else:
            self._sci_pending.append(
                __import__('simulation.ants.colony', fromlist=['_SCIEvent'])._SCIEvent(
                    r=r, c=c, t_start=t, layer=layer))
            self._sci_total += 1
            weights = self._dist_weights(nbrs, target)
            idx = int(self._rng.choice(len(nbrs), p=weights))
            new_r, new_c = nbrs[idx]

        self.positions[i] = [new_r, new_c]

        if mode == 0 and new_r == int(self.food[0]) and new_c == int(self.food[1]):
            self.modes[i] = 1
        elif mode == 1 and new_r == int(self.nest[0]) and new_c == int(self.nest[1]):
            self.modes[i] = 0
            self.food_delivered += 1


def run_pilot_calibration(delta: float, epsilon: float, seed: int,
                          pilot_steps: int = 500) -> float:
    """
    Run pilot_steps steps with a low working theta (1.0), then sample the
    end-of-run pheromone field distribution across all non-zero cells.
    Return the 25th percentile as theta_decision.

    Rationale: theta_decision separates "I can read a trail signal" from "I'm
    in unexplored territory." Sampling the post-pilot pheromone field (rather
    than recording gradient readings during movement) avoids the degenerate
    zero-argmax behavior and gives a clean distribution of actual pheromone
    magnitudes present on partially-explored terrain.

    The 25th percentile: 75% of non-zero cells in the grid have pheromone
    above this level → ant can confidently follow. 25% do not → Δ-event.
    """
    print(f"\n  Pilot calibration: delta={delta}, epsilon={epsilon}, "
          f"pilot_steps={pilot_steps}, seed={seed}")

    # Use theta=1.0 as working threshold: low enough that trails form naturally,
    # non-zero so distance heuristic is used on truly unexplored cells.
    cfg = AntConfig(delta=delta, epsilon=epsilon, seed=seed,
                    theta_decision=1.0, n_steps=pilot_steps)
    colony = ColonySimulation(cfg)
    colony.run()

    # Sample the pheromone field at end of pilot
    combined = (colony.pheromone[0] + colony.pheromone[1]).ravel()
    nonzero  = combined[combined > 0]
    if len(nonzero) == 0:
        print("  WARNING: no pheromone deposited — check delta/epsilon parameters.")
        print("  Falling back to theta_decision=1.0")
        return 1.0

    p25  = float(np.percentile(nonzero, 25))
    p50  = float(np.percentile(nonzero, 50))
    p75  = float(np.percentile(nonzero, 75))
    pmax = float(nonzero.max())
    n_cells_explored = int((combined > 0).sum())
    total_cells      = colony.H * colony.W

    print(f"  End-of-pilot pheromone field ({n_cells_explored}/{total_cells} cells non-zero):")
    print(f"    p25={p25:.4f}  p50={p50:.4f}  p75={p75:.4f}  max={pmax:.4f}")
    print(f"  => theta_decision (25th pct) = {p25:.4f}")
    print(f"     Lock this value in the preregistration before running campaigns.\n")
    return p25


# ── Smoke test ────────────────────────────────────────────────────────────────

def run_smoke_test(delta: float, epsilon: float, theta: float, seed: int,
                   save_fig: str | None, n_steps: int = 2000) -> None:
    print(f"\n  Ant colony smoke test")
    print(f"  delta={delta}  epsilon={epsilon}  theta_decision={theta}")
    print(f"  grid=50x50  n_ants=100  n_steps={n_steps}  seed={seed}\n")

    cfg = AntConfig(
        delta=delta, epsilon=epsilon, theta_decision=theta,
        n_steps=n_steps, seed=seed,
    )
    colony = ColonySimulation(cfg)

    snap_steps = [0, 499, 999, 1999]
    colony.run(snapshot_steps=snap_steps)

    # Also capture step 0 explicitly (before first step runs it's zeros; capture after)
    if 0 not in colony.snapshots:
        colony.snapshots[0] = np.zeros((cfg.grid_size, cfg.grid_size))

    # Console entropy summary
    hs = colony.entropy_history
    h_max = colony._entropy_max
    print(f"  Entropy (log2, max={h_max:.2f} bits):")
    checkpoints = [(0, "step    0"), (99, "step  100"), (499, "step  500"),
                   (999, "step 1000"), (1499, "step 1500"), (1999, "step 2000")]
    for idx, label in checkpoints:
        if idx < len(hs):
            pct = hs[idx] / h_max * 100
            bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
            print(f"    {label}: H={hs[idx]:6.3f}  [{bar}] {pct:.1f}%")

    if colony.crystallization_step is not None:
        print(f"\n  Crystallization at step {colony.crystallization_step} "
              f"(entropy < {colony._entropy_threshold:.2f} bits for "
              f"{cfg.entropy_streak} consecutive steps)")
    else:
        print(f"\n  No crystallization detected in {n_steps} steps")
        print(f"  (threshold: entropy < {colony._entropy_threshold:.2f} bits; "
              f"final entropy: {hs[-1]:.3f})")

    sci_val = colony.sci()
    print(f"\n  SCI: {sci_val}  (total Delta-events: {colony._sci_total}, "
          f"resolved: {colony._sci_resolved})")
    print(f"  Throughput: {colony.throughput():.4f} food/step  "
          f"(delivered: {colony.food_delivered})")

    # --- Four-panel heatmap ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
        fig.suptitle(
            f"Ant colony — combined pheromone (outbound + return layers)\n"
            f"delta={delta}  epsilon={epsilon}  theta={theta}  seed={seed}",
            fontsize=12
        )

        labels = ["Step 0", "Step 500", "Step 1000", "Step 2000"]
        step_keys = [0, 499, 999, 1999]

        # Global scale: max across all snapshots for consistent colormap
        all_vals = [colony.snapshots.get(k, np.zeros((cfg.grid_size, cfg.grid_size)))
                    for k in step_keys]
        vmax = max(v.max() for v in all_vals)
        vmax = max(vmax, 1e-6)

        for ax, key, label in zip(axes, step_keys, labels):
            arr = colony.snapshots.get(key, np.zeros((cfg.grid_size, cfg.grid_size)))
            im = ax.imshow(arr, origin="upper", cmap="hot", vmin=0, vmax=vmax)
            ax.set_title(label, fontsize=11)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            # Mark nest (top-left) and food (bottom-right)
            ax.plot(0, 0, "bs", markersize=8, label="nest")
            ax.plot(cfg.grid_size - 1, cfg.grid_size - 1, "g*", markersize=12, label="food")
            if key == step_keys[0]:
                ax.legend(fontsize=8, loc="upper right")

        fig.colorbar(im, ax=axes[-1], fraction=0.046, pad=0.04, label="pheromone")

        out_path = save_fig if save_fig else "ant_smoke_test.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"\n  Heatmap saved: {out_path}")

    except ImportError:
        print("\n  matplotlib not available — skipping heatmap")
    except Exception as e:
        print(f"\n  Heatmap error: {e}")

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Ant colony smoke test and pilot calibration")
    parser.add_argument("--seed",          type=int,   default=0)
    parser.add_argument("--delta",         type=float, default=0.10)
    parser.add_argument("--epsilon",       type=float, default=0.01)
    parser.add_argument("--theta",         type=float, default=None,
                        help="theta_decision (if not set, use pilot calibration value)")
    parser.add_argument("--n-steps",       type=int,   default=2000)
    parser.add_argument("--save-fig",      type=str,   default=None)
    parser.add_argument("--calibrate",     action="store_true",
                        help="Run pilot calibration only (print theta_decision, no smoke test)")
    parser.add_argument("--pilot-steps",   type=int,   default=500)
    args = parser.parse_args()

    theta = args.theta

    # Always run calibration first if theta not explicitly given
    if theta is None or args.calibrate:
        theta = run_pilot_calibration(
            delta=args.delta, epsilon=args.epsilon,
            seed=args.seed, pilot_steps=args.pilot_steps,
        )
        if args.calibrate:
            return

    run_smoke_test(
        delta=args.delta, epsilon=args.epsilon, theta=theta,
        seed=args.seed, save_fig=args.save_fig, n_steps=args.n_steps,
    )


if __name__ == "__main__":
    main()
