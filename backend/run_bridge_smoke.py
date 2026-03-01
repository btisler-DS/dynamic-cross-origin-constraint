"""Bridge formation smoke test -- Module 2.

Two tests:
  1. Fixed gap_size=10, 1000 steps.
     Confirm bridge forms, stabilizes, LOCKED count reaches equilibrium.
     Print bridge size every 100 steps.
  2. gap_size=0, 1000 steps.
     Confirm no locking occurs.

Usage
-----
  python run_bridge_smoke.py
  python run_bridge_smoke.py --gap 10 --steps 1000
  python run_bridge_smoke.py --save-fig bridge_smoke.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from simulation.ants.bridge import BridgeConfig, BridgeSimulation, LOCKED, WALKING, LEAVING


def run_fixed_gap_test(gap_size: int, n_steps: int, seed: int,
                       save_fig: str | None) -> None:
    cfg = BridgeConfig(n_ants=100, seed=seed)
    sim = BridgeSimulation(cfg, gap_size=gap_size)

    n_eq = max(1, round(cfg.reid_coefficient * gap_size))
    print(f"\n  Bridge smoke test -- fixed gap")
    print(f"  gap_size={gap_size}  corridor={cfg.corridor_width}x{cfg.corridor_length}"
          f"  n_ants={cfg.n_ants}  n_steps={n_steps}  seed={seed}")
    print(f"  gap region: col {sim.gap_start}..{sim.gap_end}"
          f"  n_equilibrium={n_eq}"
          f"  join_threshold={cfg.join_threshold}"
          f"  traffic_window={cfg.traffic_window}"
          f"  leave_patience={cfg.leave_patience}")
    print()

    checkpoint_interval = max(1, n_steps // 10)
    checkpoints = list(range(0, n_steps, checkpoint_interval)) + [n_steps - 1]

    for t in range(n_steps):
        sim.step(t)
        if t in checkpoints:
            n_lock = int((sim.states == LOCKED).sum())
            n_walk = int((sim.states == WALKING).sum())
            n_leav = int((sim.states == LEAVING).sum())
            print(f"    step {t+1:5d}: LOCKED={n_lock:3d}  WALKING={n_walk:3d}"
                  f"  LEAVING={n_leav:1d}  throughput={sim.throughput():.4f}")

    print()
    n_lock_final = int((sim.states == LOCKED).sum())
    print(f"  Final bridge size: {n_lock_final}  (n_equilibrium={n_eq})")
    if n_lock_final >= n_eq:
        print(f"  PASS: bridge formed and stabilized (>= n_equilibrium)")
    else:
        print(f"  NOTE: bridge below equilibrium target -- may need longer warmup")
    print(f"  Max bridge size: {max(sim.bridge_size_history)}")
    print(f"  Mean bridge size (last 200 steps): "
          f"{sum(sim.bridge_size_history[-200:]) / min(200, len(sim.bridge_size_history)):.1f}")
    print(f"  Throughput: {sim.throughput():.6f} round-trips/step "
          f"({sim.throughput_count} completed)")

    if save_fig:
        _plot_bridge_size(sim, gap_size, n_steps, n_eq, save_fig)


def run_zero_gap_test(n_steps: int, seed: int) -> None:
    cfg = BridgeConfig(n_ants=100, seed=seed)
    sim = BridgeSimulation(cfg, gap_size=0)

    print(f"\n  Bridge smoke test -- gap_size=0 (no gap)")
    print(f"  n_ants={cfg.n_ants}  n_steps={n_steps}  seed={seed}")
    print()

    for t in range(n_steps):
        sim.step(t)

    max_lock = max(sim.bridge_size_history)
    n_lock_final = int((sim.states == LOCKED).sum())
    print(f"  Max LOCKED during run: {max_lock}")
    print(f"  Final LOCKED count:    {n_lock_final}")
    if max_lock == 0:
        print(f"  PASS: no locking occurred with gap_size=0")
    else:
        print(f"  FAIL: unexpected locking with gap_size=0 ({max_lock} max)")
    print(f"  Throughput: {sim.throughput():.6f} round-trips/step "
          f"({sim.throughput_count} completed)")
    print()


def _plot_bridge_size(sim: BridgeSimulation, gap_size: int, n_steps: int,
                      n_eq: int, save_fig: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 4))
        steps = list(range(len(sim.bridge_size_history)))
        ax.plot(steps, sim.bridge_size_history, color="steelblue", lw=1.2,
                label="LOCKED ants")
        ax.axhline(n_eq, color="tomato", ls="--", lw=1.5,
                   label=f"n_equilibrium = {n_eq}")
        ax.set_xlabel("Step")
        ax.set_ylabel("Bridge size (LOCKED ants)")
        ax.set_title(
            f"Bridge smoke test  gap_size={gap_size}  corridor={sim.cfg.corridor_width}x{sim.cfg.corridor_length}\n"
            f"join_threshold={sim.cfg.join_threshold}  traffic_window={sim.cfg.traffic_window}"
            f"  leave_patience={sim.cfg.leave_patience}  seed={sim.cfg.seed}"
        )
        ax.legend(fontsize=9)
        plt.tight_layout()
        plt.savefig(save_fig, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"\n  Bridge size plot saved: {save_fig}")
    except ImportError:
        print("\n  matplotlib not available -- skipping plot")
    except Exception as e:
        print(f"\n  Plot error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge formation smoke test")
    parser.add_argument("--gap",      type=int,   default=10)
    parser.add_argument("--steps",    type=int,   default=1000)
    parser.add_argument("--seed",     type=int,   default=0)
    parser.add_argument("--save-fig", type=str,   default=None)
    args = parser.parse_args()

    run_fixed_gap_test(
        gap_size=args.gap, n_steps=args.steps, seed=args.seed,
        save_fig=args.save_fig,
    )
    run_zero_gap_test(n_steps=args.steps, seed=args.seed)


if __name__ == "__main__":
    main()
