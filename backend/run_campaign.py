"""Preregistered experimental campaign — Δ-Variable Theory of Interrogative Emergence.

5 conditions × 15 seeds × 500 epochs = 75 runs.

Preregistered at: https://doi.org/10.5281/zenodo.18738379
SHA-256: 7edc9113e39afb2dce430eb77802d5a6c10988e269eb823ae30e5508b12a8d6a

Conditions:
    baseline      P1  QUERY=1.5×  RESPOND=0.8×
    low_pressure  P1  QUERY=1.2×  RESPOND=0.9×
    high_pressure P1  QUERY=3.0×  RESPOND=0.5×
    extreme       P1  QUERY=5.0×  RESPOND=0.3×
    control       P0  (query disabled — flat tax only)

Seeds: 0–14 (15 independent replications per condition)

Usage:
    python run_campaign.py                         # all 75 runs, auto workers
    python run_campaign.py --workers 4             # limit parallelism
    python run_campaign.py --condition baseline    # single condition (15 runs)
    python run_campaign.py --seed 0                # single seed across all conditions
    python run_campaign.py --dry-run               # print commands, no execution
    python run_campaign.py --epochs 500 --episodes 10

Output:
    data/campaign/{condition}/seed_{seed:02d}/manifest.json
    data/campaign/{condition}/seed_{seed:02d}/run.log
    data/campaign/campaign_summary.json  (written on completion)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# ── Preregistered conditions ──────────────────────────────────────────────────

CONDITIONS: dict[str, dict] = {
    "baseline": {
        "protocol": 1,
        "declare_cost": 1.0,
        "query_cost":   1.5,
        "respond_cost": 0.8,
        "description":  "Primary confirmatory condition",
    },
    "low_pressure": {
        "protocol": 1,
        "declare_cost": 1.0,
        "query_cost":   1.2,
        "respond_cost": 0.9,
        "description":  "Cost sensitivity lower bound",
    },
    "high_pressure": {
        "protocol": 1,
        "declare_cost": 1.0,
        "query_cost":   3.0,
        "respond_cost": 0.5,
        "description":  "Cost sensitivity upper bound",
    },
    "extreme": {
        "protocol": 1,
        "declare_cost": 1.0,
        "query_cost":   5.0,
        "respond_cost": 0.3,
        "description":  "Falsification boundary",
    },
    "control": {
        "protocol": 0,
        "declare_cost": 1.0,
        "query_cost":   1.5,   # unused — P0 ignores type costs
        "respond_cost": 0.8,
        "description":  "Query-disabled reference (Protocol 0)",
    },
}

SEEDS = list(range(15))   # 0–14

# ── Run specification ─────────────────────────────────────────────────────────

@dataclass
class RunSpec:
    condition: str
    seed: int
    protocol: int
    declare_cost: float
    query_cost: float
    respond_cost: float
    epochs: int
    episodes: int
    output_dir: Path


def build_runs(
    conditions: list[str],
    seeds: list[int],
    epochs: int,
    episodes: int,
    base_output: Path,
) -> list[RunSpec]:
    runs = []
    for cname in conditions:
        c = CONDITIONS[cname]
        for seed in seeds:
            out = base_output / cname / f"seed_{seed:02d}"
            runs.append(RunSpec(
                condition=cname,
                seed=seed,
                protocol=c["protocol"],
                declare_cost=c["declare_cost"],
                query_cost=c["query_cost"],
                respond_cost=c["respond_cost"],
                epochs=epochs,
                episodes=episodes,
                output_dir=out,
            ))
    return runs


def build_command(spec: RunSpec) -> list[str]:
    return [
        sys.executable, "-u", "-m", "simulation.engine",
        "--seed",         str(spec.seed),
        "--epochs",       str(spec.epochs),
        "--episodes",     str(spec.episodes),
        "--protocol",     str(spec.protocol),
        "--declare-cost", str(spec.declare_cost),
        "--query-cost",   str(spec.query_cost),
        "--respond-cost", str(spec.respond_cost),
        "--output-dir",   str(spec.output_dir),
    ]


# ── Execution ─────────────────────────────────────────────────────────────────

def run_one(spec: RunSpec) -> dict:
    """Execute a single run. Returns result dict (used by the pool)."""
    spec.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = spec.output_dir / "run.log"
    cmd = build_command(spec)

    start = time.time()
    with open(log_path, "w") as log:
        log.write(f"# {spec.condition} seed={spec.seed} started {datetime.now().isoformat()}\n")
        log.write(f"# cmd: {' '.join(cmd)}\n\n")
        log.flush()
        result = subprocess.run(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,   # run from backend/
        )

    elapsed = time.time() - start
    status = "ok" if result.returncode == 0 else "failed"

    return {
        "condition": spec.condition,
        "seed": spec.seed,
        "status": status,
        "returncode": result.returncode,
        "elapsed_s": round(elapsed, 1),
        "output_dir": str(spec.output_dir),
    }


# ── Progress display ──────────────────────────────────────────────────────────

def fmt_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total) if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {done}/{total}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the preregistered 5-condition × 15-seed campaign."
    )
    parser.add_argument(
        "--condition", choices=list(CONDITIONS), default=None,
        help="Run a single condition only (default: all 5)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Run a single seed only (default: all 15)"
    )
    parser.add_argument(
        "--epochs", type=int, default=500,
        help="Epochs per run (default: 500)"
    )
    parser.add_argument(
        "--episodes", type=int, default=10,
        help="Episodes per epoch (default: 10)"
    )
    parser.add_argument(
        "--workers", type=int, default=None,
        help="Parallel workers (default: CPU count − 1, min 1)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Base output directory (default: ../data/campaign)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print commands without executing"
    )
    args = parser.parse_args()

    # Resolve conditions and seeds
    conditions = [args.condition] if args.condition else list(CONDITIONS)
    seeds      = [args.seed]      if args.seed is not None else SEEDS

    # Output directory — relative to backend/
    backend_dir = Path(__file__).parent
    base_output = Path(args.output_dir) if args.output_dir else backend_dir.parent / "data" / "campaign"

    # Workers
    cpu = os.cpu_count() or 2
    workers = args.workers if args.workers else max(1, cpu - 1)

    runs = build_runs(conditions, seeds, args.epochs, args.episodes, base_output)
    total = len(runs)

    print(f"\n{'=' * 60}")
    print(f"  Delta-Variable Theory -- Preregistered Campaign")
    print(f"{'=' * 60}")
    print(f"  Conditions : {', '.join(conditions)}")
    print(f"  Seeds      : {seeds[0]}-{seeds[-1]} ({len(seeds)} each)")
    print(f"  Epochs     : {args.epochs}  Episodes: {args.episodes}")
    print(f"  Total runs : {total}")
    print(f"  Workers    : {workers}")
    print(f"  Output     : {base_output}")
    print("=" * 60 + "\n")

    if args.dry_run:
        for spec in runs:
            print(" ".join(build_command(spec)))
        return

    campaign_start = time.time()
    results = []
    done = 0
    failed = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, spec): spec for spec in runs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if result["status"] != "ok":
                failed += 1
            status_icon = "OK" if result["status"] == "ok" else "!!"
            print(
                f"  {status_icon} {result['condition']:14s} seed={result['seed']:02d} "
                f"{result['elapsed_s']:6.1f}s  {fmt_bar(done, total)}"
            )

    elapsed_total = time.time() - campaign_start

    # Write campaign summary
    base_output.mkdir(parents=True, exist_ok=True)
    summary = {
        "preregistration_doi": "https://doi.org/10.5281/zenodo.18738379",
        "preregistration_sha256": "7edc9113e39afb2dce430eb77802d5a6c10988e269eb823ae30e5508b12a8d6a",
        "campaign_start": datetime.fromtimestamp(campaign_start).isoformat(),
        "campaign_end": datetime.now().isoformat(),
        "elapsed_s": round(elapsed_total, 1),
        "total_runs": total,
        "completed": done - failed,
        "failed": failed,
        "conditions": CONDITIONS,
        "seeds": seeds,
        "epochs": args.epochs,
        "episodes": args.episodes,
        "results": results,
    }
    summary_path = base_output / "campaign_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  Campaign complete: {done - failed}/{total} succeeded, {failed} failed")
    print(f"  Total time: {elapsed_total / 60:.1f} min")
    print(f"  Summary: {summary_path}")
    print("=" * 60 + "\n")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
