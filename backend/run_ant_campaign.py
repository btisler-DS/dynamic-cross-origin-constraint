"""Ant colony campaign runner — Experiments A and C.

Preregistered in: docs/preregistration-ant-modules.md (locked 2026-03-01)

Experiment A — Deposition-cost sweep:
  delta in {0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30} x 30 seeds = 210 runs
  Fixed: epsilon=0.01, tau=20, theta=0.1213, n_steps=2000

Experiment C — Coupling-window characterization:
  tau in {5, 10, 20, 40, 80} x 30 seeds = 150 runs
  Fixed: delta=0.10, epsilon=0.01, theta=0.1213, n_steps=2000
  (tau=20 condition shares parameters with Exp A delta=0.10; run independently
   for provenance. Data is interchangeable.)

Usage
-----
  python run_ant_campaign.py                   # both experiments, all runs
  python run_ant_campaign.py --exp a           # Experiment A only
  python run_ant_campaign.py --exp c           # Experiment C only
  python run_ant_campaign.py --workers 4
  python run_ant_campaign.py --seeds 0 5       # seeds 0..4
  python run_ant_campaign.py --dry-run

Output
------
  data/ant_experiments/exp_a/delta_{d}/seed_{s:02d}/manifest.json
  data/ant_experiments/exp_c/tau_{t}/seed_{s:02d}/manifest.json
  data/ant_experiments/exp_a_summary.json
  data/ant_experiments/exp_c_summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from simulation.ants.colony import AntConfig, ColonySimulation

# ── Preregistered parameters ──────────────────────────────────────────────────

THETA_DECISION = 0.1213   # locked from pilot calibration
TAU            = 20       # preregistered SCI closure window
EPSILON        = 0.01     # evaporation rate (fixed across A and C)
N_STEPS        = 2000
N_ANTS         = 100
GRID_SIZE      = 50

# Exp A: deposition-rate sweep
EXP_A_DELTAS = [0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30]

# Exp C: coupling-window sweep
EXP_C_TAUS = [5, 10, 20, 40, 80]
EXP_C_DELTA = 0.10


# ── Per-run worker ────────────────────────────────────────────────────────────

def _run_one_a(args: tuple) -> dict:
    """Run one Exp A seed. Called in subprocess via ProcessPoolExecutor."""
    delta, seed, output_dir_str = args
    cfg = AntConfig(
        delta=delta,
        epsilon=EPSILON,
        theta_decision=THETA_DECISION,
        tau=TAU,
        n_steps=N_STEPS,
        n_ants=N_ANTS,
        grid_size=GRID_SIZE,
        seed=seed,
        output_dir=output_dir_str,
    )
    colony = ColonySimulation(cfg)
    colony.run()
    colony.write_manifest()
    return {
        "delta":                delta,
        "seed":                 seed,
        "SCI":                  colony.sci(),
        "sci_total":            colony._sci_total,
        "sci_resolved":         colony._sci_resolved,
        "crystallization_step": colony.crystallization_step,
        "crystallized":         colony.crystallization_step is not None,
        "throughput":           colony.throughput(),
        "food_delivered":       colony.food_delivered,
        "final_entropy":        round(colony.entropy_history[-1], 4)
                                if colony.entropy_history else None,
    }


def _run_one_c(args: tuple) -> dict:
    """Run one Exp C seed. Called in subprocess via ProcessPoolExecutor."""
    tau, seed, output_dir_str = args
    cfg = AntConfig(
        delta=EXP_C_DELTA,
        epsilon=EPSILON,
        theta_decision=THETA_DECISION,
        tau=tau,
        n_steps=N_STEPS,
        n_ants=N_ANTS,
        grid_size=GRID_SIZE,
        seed=seed,
        output_dir=output_dir_str,
    )
    colony = ColonySimulation(cfg)
    colony.run()
    colony.write_manifest()
    return {
        "tau":                  tau,
        "seed":                 seed,
        "SCI":                  colony.sci(),
        "sci_total":            colony._sci_total,
        "sci_resolved":         colony._sci_resolved,
        "crystallization_step": colony.crystallization_step,
        "crystallized":         colony.crystallization_step is not None,
        "throughput":           colony.throughput(),
    }


# ── Campaign runners ──────────────────────────────────────────────────────────

def run_exp_a(seeds: list[int], workers: int, dry_run: bool,
              data_root: Path) -> list[dict]:
    """Run Experiment A: deposition sweep."""
    out_root = data_root / "exp_a"
    jobs = []
    for delta in EXP_A_DELTAS:
        delta_tag = f"delta_{delta:.2f}".replace(".", "_")
        for seed in seeds:
            out_dir = out_root / delta_tag / f"seed_{seed:02d}"
            if not dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
            jobs.append((delta, seed, str(out_dir)))

    print(f"\nExp A -- deposition sweep")
    print(f"  deltas: {EXP_A_DELTAS}")
    print(f"  seeds:  {seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)")
    print(f"  total:  {len(jobs)} runs  |  workers: {workers}")
    print(f"  output: {out_root}")

    if dry_run:
        for delta, seed, out_dir in jobs[:5]:
            print(f"  DRY-RUN: delta={delta}  seed={seed}  -> {out_dir}")
        if len(jobs) > 5:
            print(f"  ... ({len(jobs) - 5} more)")
        return []

    results = []
    t0 = time.time()
    done = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one_a, job): job for job in jobs}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
                done += 1
                crys = "CRYS" if r["crystallized"] else "    "
                print(f"  [{done:3d}/{len(jobs)}] {crys}  delta={r['delta']:.2f}"
                      f"  seed={r['seed']:02d}  SCI={str(r['SCI']):6s}"
                      f"  crys@{str(r['crystallization_step']):6s}"
                      f"  tp={r['throughput']:.4f}")
            except Exception as e:
                job = futures[fut]
                print(f"  ERROR: delta={job[0]}  seed={job[1]}: {e}")

    elapsed = time.time() - t0
    print(f"\nExp A done: {done}/{len(jobs)} runs in {elapsed:.0f}s")
    return results


def run_exp_c(seeds: list[int], workers: int, dry_run: bool,
              data_root: Path) -> list[dict]:
    """Run Experiment C: coupling-window characterization."""
    out_root = data_root / "exp_c"
    jobs = []
    for tau in EXP_C_TAUS:
        for seed in seeds:
            out_dir = out_root / f"tau_{tau}" / f"seed_{seed:02d}"
            if not dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
            jobs.append((tau, seed, str(out_dir)))

    print(f"\nExp C -- coupling-window characterization")
    print(f"  taus:   {EXP_C_TAUS}")
    print(f"  seeds:  {seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)")
    print(f"  total:  {len(jobs)} runs  |  workers: {workers}")
    print(f"  output: {out_root}")

    if dry_run:
        for tau, seed, out_dir in jobs[:5]:
            print(f"  DRY-RUN: tau={tau}  seed={seed}  -> {out_dir}")
        if len(jobs) > 5:
            print(f"  ... ({len(jobs) - 5} more)")
        return []

    results = []
    t0 = time.time()
    done = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one_c, job): job for job in jobs}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
                done += 1
                print(f"  [{done:3d}/{len(jobs)}]  tau={r['tau']:3d}"
                      f"  seed={r['seed']:02d}  SCI={str(r['SCI']):6s}")
            except Exception as e:
                job = futures[fut]
                print(f"  ERROR: tau={job[0]}  seed={job[1]}: {e}")

    elapsed = time.time() - t0
    print(f"\nExp C done: {done}/{len(jobs)} runs in {elapsed:.0f}s")
    return results


# ── Summary writers ───────────────────────────────────────────────────────────

def write_summary_a(results: list[dict], data_root: Path) -> None:
    """Aggregate Exp A results by delta level and write summary JSON."""
    by_delta: dict[float, list[dict]] = {}
    for r in results:
        by_delta.setdefault(r["delta"], []).append(r)

    summary = {
        "experiment":       "A",
        "description":      "Deposition-cost sweep",
        "generated":        datetime.now().isoformat(),
        "preregistration":  "docs/preregistration-ant-modules.md",
        "fixed_params": {
            "epsilon":        EPSILON,
            "tau":            TAU,
            "theta_decision": THETA_DECISION,
            "n_steps":        N_STEPS,
            "n_ants":         N_ANTS,
            "grid_size":      GRID_SIZE,
        },
        "conditions": [],
    }

    for delta in EXP_A_DELTAS:
        runs = by_delta.get(delta, [])
        if not runs:
            continue
        n = len(runs)
        crys = [r for r in runs if r["crystallized"]]
        sci_vals = [r["SCI"] for r in runs if r["SCI"] is not None]
        crys_epochs = [r["crystallization_step"] for r in crys]
        throughputs = [r["throughput"] for r in runs]
        entropies = [r["final_entropy"] for r in runs if r["final_entropy"] is not None]

        summary["conditions"].append({
            "delta":                    delta,
            "n_seeds":                  n,
            "crystallization_rate":     round(len(crys) / n, 4),
            "n_crystallized":           len(crys),
            "mean_crystallization_epoch": round(sum(crys_epochs) / len(crys_epochs), 1)
                                          if crys_epochs else None,
            "sd_crystallization_epoch": round(
                (sum((x - sum(crys_epochs)/len(crys_epochs))**2
                     for x in crys_epochs) / len(crys_epochs)) ** 0.5, 1
            ) if len(crys_epochs) > 1 else None,
            "mean_SCI":                 round(sum(sci_vals) / len(sci_vals), 4)
                                        if sci_vals else None,
            "mean_throughput":          round(sum(throughputs) / len(throughputs), 6),
            "mean_final_entropy":       round(sum(entropies) / len(entropies), 4)
                                        if entropies else None,
        })

    out = data_root / "exp_a_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nExp A summary: {out}")

    # Print table
    print(f"\n  {'delta':>7}  {'crys_rate':>9}  {'crys_epoch':>10}  "
          f"{'SCI':>6}  {'throughput':>10}")
    for cond in summary["conditions"]:
        epoch_str = (f"{cond['mean_crystallization_epoch']:.0f}"
                     if cond["mean_crystallization_epoch"] else "  N/A ")
        sci_str = (f"{cond['mean_SCI']:.4f}" if cond["mean_SCI"] is not None else "  N/A")
        print(f"  {cond['delta']:>7.2f}  {cond['crystallization_rate']:>9.3f}"
              f"  {epoch_str:>10}  {sci_str:>6}  {cond['mean_throughput']:>10.6f}")


def write_summary_c(results: list[dict], data_root: Path) -> None:
    """Aggregate Exp C results by tau level and write summary JSON."""
    by_tau: dict[int, list[dict]] = {}
    for r in results:
        by_tau.setdefault(r["tau"], []).append(r)

    summary = {
        "experiment":       "C",
        "description":      "Coupling-window characterization",
        "generated":        datetime.now().isoformat(),
        "preregistration":  "docs/preregistration-ant-modules.md",
        "fixed_params": {
            "delta":          EXP_C_DELTA,
            "epsilon":        EPSILON,
            "theta_decision": THETA_DECISION,
            "n_steps":        N_STEPS,
            "n_ants":         N_ANTS,
            "grid_size":      GRID_SIZE,
        },
        "conditions": [],
    }

    for tau in EXP_C_TAUS:
        runs = by_tau.get(tau, [])
        if not runs:
            continue
        n = len(runs)
        sci_vals = [r["SCI"] for r in runs if r["SCI"] is not None]
        mean_sci = round(sum(sci_vals) / len(sci_vals), 4) if sci_vals else None
        sd_sci = round(
            (sum((x - mean_sci) ** 2 for x in sci_vals) / len(sci_vals)) ** 0.5, 4
        ) if sci_vals and len(sci_vals) > 1 and mean_sci is not None else None

        summary["conditions"].append({
            "tau":      tau,
            "n_seeds":  n,
            "mean_SCI": mean_sci,
            "sd_SCI":   sd_sci,
            "n_with_events": sum(1 for r in runs if r["sci_total"] > 0),
        })

    out = data_root / "exp_c_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nExp C summary: {out}")

    print(f"\n  {'tau':>5}  {'mean_SCI':>8}  {'sd_SCI':>7}  {'n_events':>9}")
    for cond in summary["conditions"]:
        sci_str  = f"{cond['mean_SCI']:.4f}" if cond["mean_SCI"] is not None else "   N/A"
        sd_str   = f"{cond['sd_SCI']:.4f}"   if cond["sd_SCI"] is not None  else "   N/A"
        print(f"  {cond['tau']:>5}  {sci_str:>8}  {sd_str:>7}  {cond['n_with_events']:>9}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ant colony campaign runner (Experiments A and C)"
    )
    parser.add_argument("--exp",      choices=["a", "c", "both"], default="both",
                        help="Which experiment to run")
    parser.add_argument("--workers",  type=int, default=None,
                        help="Number of parallel workers (default: cpu_count)")
    parser.add_argument("--seeds",    type=int, nargs=2, default=[0, 30],
                        metavar=("START", "END"),
                        help="Seed range [start, end) (default: 0 30)")
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--data-dir", type=str,
                        default=str(Path(__file__).parent.parent / "data" / "ant_experiments"))
    args = parser.parse_args()

    seeds   = list(range(args.seeds[0], args.seeds[1]))
    workers = args.workers or max(1, (os.cpu_count() or 4) - 1)
    data_root = Path(args.data_dir)

    if not args.dry_run:
        data_root.mkdir(parents=True, exist_ok=True)

    print(f"Ant colony campaign  --  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]}  Workers: {workers}  Data: {data_root}")

    run_a = args.exp in ("a", "both")
    run_c = args.exp in ("c", "both")

    if run_a:
        results_a = run_exp_a(seeds, workers, args.dry_run, data_root)
        if results_a:
            write_summary_a(results_a, data_root)

    if run_c:
        results_c = run_exp_c(seeds, workers, args.dry_run, data_root)
        if results_c:
            write_summary_c(results_c, data_root)

    print("\nDone.")


if __name__ == "__main__":
    main()
