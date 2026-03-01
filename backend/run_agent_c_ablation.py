"""Experiment 6 — Agent C Ablation campaign runner.

Tests preregistered prediction P4: does removing Agent C's ability to
interrogate dissolve or redirect the coordination structure?

Design:
    5 seeds (0–4) from the baseline condition (query_cost=1.5×).
    Agent C's type_head is frozen to DECLARE-only (same mechanism as Protocol 0
    for that agent). Agents A and B retain full type_head gradient.
    500 epochs, 10 episodes — identical to the confirmatory campaign.

Comparison baseline:
    data/campaign/baseline/seed_{seed:02d}/manifest.json (preregistered campaign).

Pass (P4 confirmed — structural hub): C-ablated runs crystallise less often or
    later, QRC is lower, confirming Agent C played a structural broker role.
Fail (P4 rejected — no privileged hub): C-ablated runs crystallise at the same
    rate and speed; another agent compensates as coordinator.

Output:
    data/agent_c_ablation/seed_{seed:02d}/manifest.json
    data/agent_c_ablation/seed_{seed:02d}/run.log
    data/agent_c_ablation/ablation_summary.json

Usage:
    python run_agent_c_ablation.py                  # all 5 seeds
    python run_agent_c_ablation.py --workers 3
    python run_agent_c_ablation.py --seed 0
    python run_agent_c_ablation.py --dry-run
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

ABLATION_SEEDS = list(range(5))   # 0–4

# Baseline condition — identical to preregistered campaign
PROTOCOL      = 1
DECLARE_COST  = 1.0
QUERY_COST    = 1.5
RESPOND_COST  = 0.8
EPOCHS        = 500
EPISODES      = 10


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_baseline_manifest(seed: int, base_dir: Path) -> dict | None:
    path = base_dir / "campaign" / "baseline" / f"seed_{seed:02d}" / "manifest.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def fmt_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total) if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {done}/{total}"


# ── Single-seed runner ────────────────────────────────────────────────────────

def run_one(spec: dict) -> dict:
    """Execute one ablated seed as a subprocess and return result metadata."""
    seed     = spec["seed"]
    out      = Path(spec["output_dir"])
    log_path = out / "run.log"
    out.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-u", "-m", "simulation.engine",
        "--seed",         str(seed),
        "--epochs",       str(spec["epochs"]),
        "--episodes",     str(spec["episodes"]),
        "--protocol",     str(spec["protocol"]),
        "--declare-cost", str(spec["declare_cost"]),
        "--query-cost",   str(spec["query_cost"]),
        "--respond-cost", str(spec["respond_cost"]),
        "--output-dir",   str(out),
        "--ablate-agent-c",
    ]

    start = time.time()
    with open(log_path, "w") as log:
        log.write(
            f"# Experiment 6: Agent C Ablation — seed={seed}  "
            f"started {datetime.now().isoformat()}\n"
            f"# cmd: {' '.join(cmd)}\n\n"
        )
        log.flush()
        proc = subprocess.run(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,
        )

    elapsed = time.time() - start
    status  = "ok" if proc.returncode == 0 else "failed"

    # Read the manifest written by the engine
    manifest_path = out / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    crys_epoch = manifest.get("crystallization_epoch")
    final      = manifest.get("final_metrics", {})

    return {
        "seed":                 seed,
        "status":               status,
        "returncode":           proc.returncode,
        "elapsed_s":            round(elapsed, 1),
        "output_dir":           str(out),
        "crystallization_epoch": crys_epoch,
        "crystallized":         crys_epoch is not None,
        "final_entropy":        final.get("type_entropy"),
        "final_qrc":            final.get("qrc"),
        "final_survival":       final.get("survival_rate"),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 6: Agent C Ablation — P4 test"
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="Run a single seed (default: all 5)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Parallel workers (default: CPU count − 1, min 1)")
    parser.add_argument("--epochs",   type=int, default=EPOCHS)
    parser.add_argument("--episodes", type=int, default=EPISODES)
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Base output dir (default: ../data/agent_c_ablation)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing")
    args = parser.parse_args()

    seeds = [args.seed] if args.seed is not None else ABLATION_SEEDS

    backend_dir = Path(__file__).parent
    data_dir    = backend_dir.parent / "data"
    base_output = (
        Path(args.output_dir) if args.output_dir
        else data_dir / "agent_c_ablation"
    )

    cpu     = os.cpu_count() or 2
    workers = args.workers if args.workers else max(1, cpu - 1)

    specs = [
        {
            "seed":         seed,
            "output_dir":   str(base_output / f"seed_{seed:02d}"),
            "protocol":     PROTOCOL,
            "declare_cost": DECLARE_COST,
            "query_cost":   QUERY_COST,
            "respond_cost": RESPOND_COST,
            "epochs":       args.epochs,
            "episodes":     args.episodes,
        }
        for seed in seeds
    ]
    total = len(specs)

    # Load baseline manifests for comparison display
    baseline = {s: _load_baseline_manifest(s, data_dir) for s in seeds}

    print(f"\n{'=' * 60}")
    print(f"  Experiment 6: Agent C Ablation — P4 Prediction")
    print(f"{'=' * 60}")
    print(f"  Seeds          : {seeds[0]}-{seeds[-1]} ({len(seeds)} runs)")
    print(f"  Condition      : Protocol 1, q={QUERY_COST}× (baseline)")
    print(f"  Ablation       : Agent C type_head frozen to DECLARE-only")
    print(f"  Epochs/episodes: {args.epochs} / {args.episodes}")
    print(f"  Workers        : {workers}")
    print(f"  Output         : {base_output}")
    print(f"\n  Baseline reference (preregistered campaign):")
    for s in seeds:
        m = baseline.get(s)
        if m:
            crys = m.get("crystallization_epoch", "—")
            fm   = m.get("final_metrics", {})
            print(
                f"    seed={s:02d}  crys_ep={str(crys):>4s}  "
                f"H={fm.get('type_entropy', 0):.3f}  QRC={fm.get('qrc', 0):.3f}"
            )
        else:
            print(f"    seed={s:02d}  (no baseline manifest found)")
    print("=" * 60 + "\n")

    if args.dry_run:
        for spec in specs:
            cmd = [
                sys.executable, "-u", "-m", "simulation.engine",
                "--seed", str(spec["seed"]),
                "--epochs", str(spec["epochs"]),
                "--episodes", str(spec["episodes"]),
                "--protocol", str(spec["protocol"]),
                "--declare-cost", str(spec["declare_cost"]),
                "--query-cost", str(spec["query_cost"]),
                "--respond-cost", str(spec["respond_cost"]),
                "--output-dir", spec["output_dir"],
                "--ablate-agent-c",
            ]
            print(" ".join(cmd))
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

            crys      = result.get("crystallization_epoch")
            h_abl     = result.get("final_entropy")
            qrc_abl   = result.get("final_qrc")

            # Pull baseline values for inline comparison
            bm     = baseline.get(result["seed"], {}) or {}
            b_crys = bm.get("crystallization_epoch")
            bfm    = bm.get("final_metrics", {})
            b_qrc  = bfm.get("qrc")

            delta_crys = (
                f"+{crys - b_crys}" if crys is not None and b_crys is not None and crys > b_crys
                else f"{crys - b_crys}" if crys is not None and b_crys is not None
                else "N/A"
            )

            icon = "OK" if result["status"] == "ok" else "!!"
            print(
                f"  {icon} seed={result['seed']:02d}"
                f"  crys_ep={str(crys):>4s} (base={str(b_crys):>4s}, d={delta_crys:>6s})"
                f"  QRC_abl={str(round(qrc_abl, 3)) if qrc_abl else 'N/A':>6s}"
                f"  QRC_base={str(round(b_qrc, 3)) if b_qrc else 'N/A':>6s}"
                f"  {result['elapsed_s']:6.1f}s  {fmt_bar(done, total)}"
            )

    elapsed_total = time.time() - campaign_start

    # ── Aggregate comparison ───────────────────────────────────────────────────
    crystallized_ablated  = [r for r in results if r.get("crystallized")]
    crystallized_baseline = [
        s for s in seeds
        if (baseline.get(s) or {}).get("crystallization_epoch") is not None
    ]

    # Mean crystallization delay
    delays = []
    for r in crystallized_ablated:
        bm = baseline.get(r["seed"]) or {}
        b_crys = bm.get("crystallization_epoch")
        a_crys = r["crystallization_epoch"]
        if b_crys is not None and a_crys is not None:
            delays.append(a_crys - b_crys)

    mean_delay = round(sum(delays) / len(delays), 1) if delays else None

    # Mean QRC delta
    qrc_deltas = []
    for r in results:
        bm = baseline.get(r["seed"]) or {}
        b_qrc = (bm.get("final_metrics") or {}).get("qrc")
        a_qrc = r.get("final_qrc")
        if b_qrc is not None and a_qrc is not None:
            qrc_deltas.append(a_qrc - b_qrc)

    mean_qrc_delta = round(sum(qrc_deltas) / len(qrc_deltas), 4) if qrc_deltas else None

    summary = {
        "experiment":               "agent_c_ablation",
        "preregistered_prediction": "P4",
        "campaign_date":            datetime.now().isoformat(),
        "elapsed_s":                round(elapsed_total, 1),
        "total_seeds":              total,
        "completed":                done - failed,
        "failed":                   failed,
        "ablation":                 "agent_c_type_head_frozen_to_DECLARE",
        "condition":                "baseline_q1.5",
        "epochs":                   args.epochs,
        "crystallized_ablated":     len(crystallized_ablated),
        "crystallized_baseline":    len(crystallized_baseline),
        "crystallization_rate_ablated":  round(len(crystallized_ablated) / total, 4),
        "crystallization_rate_baseline": round(len(crystallized_baseline) / total, 4),
        "mean_crystallization_delay_epochs": mean_delay,
        "mean_qrc_delta":           mean_qrc_delta,
        "seed_results":             sorted(results, key=lambda r: r["seed"]),
    }

    base_output.mkdir(parents=True, exist_ok=True)
    summary_path = base_output / "ablation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    crys_rate_abl  = len(crystallized_ablated) / total
    crys_rate_base = len(crystallized_baseline) / total

    print(f"\n{'=' * 60}")
    print(f"  Experiment 6 complete")
    print(f"  Seeds run          : {done}/{total}  ({failed} failed)")
    print(f"  Crystallised (abl) : {len(crystallized_ablated)}/{total}  ({crys_rate_abl:.0%})")
    print(f"  Crystallised (base): {len(crystallized_baseline)}/{total}  ({crys_rate_base:.0%})")
    if mean_delay is not None:
        delay_str = f"+{mean_delay}" if mean_delay > 0 else str(mean_delay)
        print(f"  Mean crys. delay   : {delay_str} epochs")
    if mean_qrc_delta is not None:
        print(f"  Mean QRC delta     : {mean_qrc_delta:+.4f}")
    if crys_rate_abl < crys_rate_base or (mean_delay is not None and mean_delay > 20):
        print(f"  P4 verdict         : CONFIRMED (Agent C plays structural role)")
    else:
        print(f"  P4 verdict         : NOT CONFIRMED (system compensates without C)")
    print(f"  Total time         : {elapsed_total / 60:.1f} min")
    print(f"  Summary            : {summary_path}")
    print("=" * 60 + "\n")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
