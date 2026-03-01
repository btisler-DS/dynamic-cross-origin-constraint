"""Experiment 2 — Hysteresis Sweep campaign runner.

Tests preregistered prediction P3: does a crystallised interrogative protocol
persist when query cost is reduced below the formation threshold?

Design:
    Seeds 0-13 (14 runs — the seeds that crystallised in the baseline condition;
    seed 14 is omitted as the non-crystalliser).
    Phase 1: Protocol 1, query_cost=1.5×, run until H < 0.95 for 5 consecutive
             epochs, then 10 grace epochs.
    Phase 2: Freeze all agent parameters. Reduce to query_cost=1.2× (low_pressure).
             Run 100 epochs. No gradient updates.

Pass: H < 0.95 for ≥ 80% of phase-2 epochs in a seed → hysteresis confirmed.
Fail: H rebounds above 0.95 quickly → falsifies P3.

Output:
    data/hysteresis/seed_{seed:02d}/hysteresis_manifest.json
    data/hysteresis/seed_{seed:02d}/run.log
    data/hysteresis/hysteresis_summary.json

Usage:
    python run_hysteresis.py                  # all 14 seeds, auto workers
    python run_hysteresis.py --workers 4
    python run_hysteresis.py --seed 0         # single seed
    python run_hysteresis.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Seeds that crystallised in the preregistered baseline campaign (seed 14 did not)
HYSTERESIS_SEEDS = list(range(14))   # 0–13

PHASE1_QUERY_COST   = 1.5   # formation condition (preregistered baseline)
PHASE1_RESPOND_COST = 0.8
PHASE2_QUERY_COST   = 1.2   # below-formation (preregistered low_pressure)
PHASE2_RESPOND_COST = 0.9
MAX_PHASE1_EPOCHS   = 300
GRACE_EPOCHS        = 10
PHASE2_EPOCHS       = 100
EPISODES            = 10


# ── Single-run entry point ────────────────────────────────────────────────────

def _run_seed(
    seed: int,
    output_dir: Path,
    max_phase1_epochs: int,
    grace_epochs: int,
    phase2_epochs: int,
    episodes: int,
) -> dict:
    """Execute one hysteresis run in-process (called by the worker pool)."""
    # Import here so each worker gets a fresh torch state
    from simulation.experiments.hysteresis_engine import HysteresisConfig, HysteresisEngine

    config = HysteresisConfig(
        seed=seed,
        phase1_query_cost=PHASE1_QUERY_COST,
        phase1_respond_cost=PHASE1_RESPOND_COST,
        phase2_query_cost=PHASE2_QUERY_COST,
        phase2_respond_cost=PHASE2_RESPOND_COST,
        max_phase1_epochs=max_phase1_epochs,
        grace_epochs=grace_epochs,
        phase2_epochs=phase2_epochs,
        episodes_per_epoch=episodes,
        output_dir=str(output_dir),
    )
    engine = HysteresisEngine(config)
    return engine.run()


def run_one(spec: dict) -> dict:
    """Top-level worker function — runs one seed and returns result metadata."""
    seed       = spec["seed"]
    out        = Path(spec["output_dir"])
    log_path   = out / "run.log"
    out.mkdir(parents=True, exist_ok=True)

    start = time.time()
    # Spawn a subprocess so each run gets an isolated Python/torch context
    cmd = [
        sys.executable, "-u", "-c",
        f"""
import sys
sys.path.insert(0, r'{Path(__file__).parent}')
from simulation.experiments.hysteresis_engine import HysteresisConfig, HysteresisEngine
import json, os
config = HysteresisConfig(
    seed={seed},
    phase1_query_cost={spec['phase1_query_cost']},
    phase1_respond_cost={spec['phase1_respond_cost']},
    phase2_query_cost={spec['phase2_query_cost']},
    phase2_respond_cost={spec['phase2_respond_cost']},
    max_phase1_epochs={spec['max_phase1_epochs']},
    grace_epochs={spec['grace_epochs']},
    phase2_epochs={spec['phase2_epochs']},
    episodes_per_epoch={spec['episodes']},
    output_dir=r'{out}',
)
engine = HysteresisEngine(config)
manifest = engine.run()
print(json.dumps({{
    'crystallized': manifest['crystallized'],
    'crystallization_epoch': manifest['crystallization_epoch'],
    'hysteresis_detected': manifest['hysteresis_detected'],
    'persistence_rate': manifest['persistence_rate'],
    'final_phase2_entropy': manifest['final_phase2_entropy'],
    'final_phase2_qrc': manifest['final_phase2_qrc'],
    'phase2_epochs_run': manifest['phase2_epochs_run'],
}}))
""",
    ]

    with open(log_path, "w") as log:
        log.write(
            f"# Experiment 2: Hysteresis — seed={seed}  started {datetime.now().isoformat()}\n"
            f"# phase1_q={spec['phase1_query_cost']} -> phase2_q={spec['phase2_query_cost']}\n\n"
        )
        log.flush()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        log.write(proc.stdout)
        if proc.stderr:
            log.write("\n--- stderr ---\n")
            log.write(proc.stderr)

    elapsed = time.time() - start

    # Parse the JSON summary line printed by the subprocess
    manifest_summary = {}
    for line in reversed(proc.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                manifest_summary = json.loads(line)
            except json.JSONDecodeError:
                pass
            break

    return {
        "seed": seed,
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "elapsed_s": round(elapsed, 1),
        "output_dir": str(out),
        **manifest_summary,
    }


# ── Progress bar ──────────────────────────────────────────────────────────────

def fmt_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total) if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {done}/{total}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 2: Hysteresis Sweep — P3 test"
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="Run a single seed (default: all 14)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Parallel workers (default: CPU count − 1, min 1)")
    parser.add_argument("--max-phase1-epochs", type=int, default=MAX_PHASE1_EPOCHS)
    parser.add_argument("--grace-epochs",      type=int, default=GRACE_EPOCHS)
    parser.add_argument("--phase2-epochs",     type=int, default=PHASE2_EPOCHS)
    parser.add_argument("--episodes",          type=int, default=EPISODES)
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Base output dir (default: ../data/hysteresis)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print config without executing")
    args = parser.parse_args()

    seeds = [args.seed] if args.seed is not None else HYSTERESIS_SEEDS

    backend_dir = Path(__file__).parent
    base_output = (
        Path(args.output_dir) if args.output_dir
        else backend_dir.parent / "data" / "hysteresis"
    )

    cpu     = os.cpu_count() or 2
    workers = args.workers if args.workers else max(1, cpu - 1)

    specs = [
        {
            "seed":                seed,
            "output_dir":          str(base_output / f"seed_{seed:02d}"),
            "phase1_query_cost":   PHASE1_QUERY_COST,
            "phase1_respond_cost": PHASE1_RESPOND_COST,
            "phase2_query_cost":   PHASE2_QUERY_COST,
            "phase2_respond_cost": PHASE2_RESPOND_COST,
            "max_phase1_epochs":   args.max_phase1_epochs,
            "grace_epochs":        args.grace_epochs,
            "phase2_epochs":       args.phase2_epochs,
            "episodes":            args.episodes,
        }
        for seed in seeds
    ]
    total = len(specs)

    print(f"\n{'=' * 60}")
    print(f"  Experiment 2: Hysteresis Sweep — P3 Prediction")
    print(f"{'=' * 60}")
    print(f"  Seeds          : {seeds[0]}-{seeds[-1]} ({len(seeds)} runs)")
    print(f"  Phase 1 q cost : {PHASE1_QUERY_COST}×  (formation threshold)")
    print(f"  Phase 2 q cost : {PHASE2_QUERY_COST}×  (below threshold — low_pressure)")
    print(f"  Max P1 epochs  : {args.max_phase1_epochs}  Grace: {args.grace_epochs}")
    print(f"  Phase 2 epochs : {args.phase2_epochs}")
    print(f"  Workers        : {workers}")
    print(f"  Output         : {base_output}")
    print("=" * 60 + "\n")

    if args.dry_run:
        for s in specs:
            print(f"  seed={s['seed']:02d}  out={s['output_dir']}")
        return

    campaign_start = time.time()
    results        = []
    done = failed  = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, spec): spec for spec in specs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done += 1
            if result["status"] != "ok":
                failed += 1

            hyst = result.get("hysteresis_detected")
            pers = result.get("persistence_rate")
            crys = result.get("crystallization_epoch")
            icon = "OK" if result["status"] == "ok" else "!!"
            hyst_str = (
                f"  HYSTERESIS={'YES' if hyst else 'NO ':3s}  persist={pers:.2f}"
                if pers is not None else "  (no crystallisation)"
            )
            print(
                f"  {icon} seed={result['seed']:02d}  crys_ep={str(crys):>4s}"
                f"{hyst_str}  {result['elapsed_s']:6.1f}s  {fmt_bar(done, total)}"
            )

    elapsed_total = time.time() - campaign_start

    # ── Aggregate summary ──────────────────────────────────────────────────────
    crystallized_runs = [r for r in results if r.get("crystallized")]
    hysteresis_yes    = [r for r in crystallized_runs if r.get("hysteresis_detected")]

    summary = {
        "experiment":           "hysteresis",
        "preregistered_prediction": "P3",
        "campaign_date":        datetime.now().isoformat(),
        "elapsed_s":            round(elapsed_total, 1),
        "total_seeds":          total,
        "completed":            done - failed,
        "failed":               failed,
        "crystallized":         len(crystallized_runs),
        "hysteresis_confirmed": len(hysteresis_yes),
        "hysteresis_rate":      round(len(hysteresis_yes) / len(crystallized_runs), 4)
                                if crystallized_runs else None,
        "phase1_query_cost":    PHASE1_QUERY_COST,
        "phase2_query_cost":    PHASE2_QUERY_COST,
        "grace_epochs":         args.grace_epochs,
        "phase2_epochs":        args.phase2_epochs,
        "pass_threshold":       0.80,
        "seed_results":         results,
    }

    base_output.mkdir(parents=True, exist_ok=True)
    summary_path = base_output / "hysteresis_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  Experiment 2 complete")
    print(f"  Seeds run         : {done}/{total}  ({failed} failed)")
    print(f"  Crystallised      : {len(crystallized_runs)}/{done}")
    if crystallized_runs:
        rate = len(hysteresis_yes) / len(crystallized_runs)
        verdict = "CONFIRMED" if rate >= 0.7 else "NOT CONFIRMED"
        print(f"  Hysteresis        : {len(hysteresis_yes)}/{len(crystallized_runs)}  ({rate:.0%})  -> P3 {verdict}")
    print(f"  Total time        : {elapsed_total / 60:.1f} min")
    print(f"  Summary           : {summary_path}")
    print("=" * 60 + "\n")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
