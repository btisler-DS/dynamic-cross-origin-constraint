"""Preregistration P4 — Substrate Independence campaign and analysis.

Tests: do heterogeneous agents (RNN/CNN/GNN) each participate in
query-response coupling with no significant architectural differences
in convergence rate? (ANOVA, p > 0.10 = pass; p <= 0.10 = fail)

Design:
    15 baseline seeds (0-14), Protocol 1, q=1.5x — identical to the
    preregistered campaign but now with per-agent type tracking written
    to the manifest.

Primary outcome variables (preregistration §Substrate Metrics):
    9.  Architecture Convergence: per-agent crystallisation epoch
        (first 5-streak where agent's QUERY fraction > 5%).
        One-way ANOVA across A (RNN), B (CNN), C (GNN).
    10. Cross-Architecture Coupling: per-agent QUERY and RESPOND
        participation fractions from final 50 crystallised epochs.

Pass: ANOVA p > 0.10 on convergence epoch (no significant arch difference).
Fail: ANOVA p <= 0.10 (significant arch difference in convergence timing).
Note: Agent C signal-type proportions are explicitly excluded from
      falsification per preregistration §Statistical Analysis Plan.

Output:
    data/p4_substrate/seed_{seed:02d}/manifest.json
    data/p4_substrate/seed_{seed:02d}/run.log
    data/p4_substrate/p4_summary.json

Usage:
    python run_p4_substrate.py                  # all 15 seeds
    python run_p4_substrate.py --workers 4
    python run_p4_substrate.py --seed 0
    python run_p4_substrate.py --dry-run
    python run_p4_substrate.py --analyze-only   # rerun analysis on existing data
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

import scipy.stats as stats

SEEDS    = list(range(15))
PROTOCOL = 1
DECLARE_COST  = 1.0
QUERY_COST    = 1.5
RESPOND_COST  = 0.8
EPOCHS   = 500
EPISODES = 10

ANOVA_ALPHA = 0.10          # preregistered significance threshold
QUERY_PARTICIPATION_WINDOW = 50   # final N crystallised epochs for participation rate


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total) if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {done}/{total}"


# ── Single-seed runner ────────────────────────────────────────────────────────

def run_one(spec: dict) -> dict:
    out      = Path(spec["output_dir"])
    log_path = out / "run.log"
    out.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-u", "-m", "simulation.engine",
        "--seed",         str(spec["seed"]),
        "--epochs",       str(spec["epochs"]),
        "--episodes",     str(spec["episodes"]),
        "--protocol",     str(spec["protocol"]),
        "--declare-cost", str(spec["declare_cost"]),
        "--query-cost",   str(spec["query_cost"]),
        "--respond-cost", str(spec["respond_cost"]),
        "--output-dir",   str(out),
    ]

    start = time.time()
    with open(log_path, "w") as log:
        log.write(
            f"# P4 Substrate Independence — seed={spec['seed']}  "
            f"started {datetime.now().isoformat()}\n"
            f"# cmd: {' '.join(cmd)}\n\n"
        )
        log.flush()
        proc = subprocess.run(
            cmd, stdout=log, stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,
        )

    elapsed = time.time() - start
    status  = "ok" if proc.returncode == 0 else "failed"

    manifest_path = out / "manifest.json"
    manifest = json.load(open(manifest_path)) if manifest_path.exists() else {}

    pac = manifest.get("per_agent_crystallization", {})
    return {
        "seed":    spec["seed"],
        "status":  status,
        "elapsed_s": round(elapsed, 1),
        "crystallization_epoch":     manifest.get("crystallization_epoch"),
        "per_agent_crystallization": pac,
        "A_crys": pac.get("A"),
        "B_crys": pac.get("B"),
        "C_crys": pac.get("C"),
    }


# ── Analysis ──────────────────────────────────────────────────────────────────

def _load_manifests(base_output: Path, seeds: list[int]) -> list[dict]:
    manifests = []
    for seed in seeds:
        p = base_output / f"seed_{seed:02d}" / "manifest.json"
        if p.exists():
            manifests.append(json.load(open(p)))
    return manifests


def run_analysis(base_output: Path, seeds: list[int]) -> dict:
    """Load manifests, run preregistered P4 analysis, return results dict."""
    manifests = _load_manifests(base_output, seeds)
    if not manifests:
        return {"error": "No manifests found"}

    # ── 1. Per-agent convergence epoch (ANOVA) ─────────────────────────────
    A_epochs, B_epochs, C_epochs = [], [], []
    for m in manifests:
        pac = m.get("per_agent_crystallization", {})
        if pac.get("A") is not None: A_epochs.append(pac["A"])
        if pac.get("B") is not None: B_epochs.append(pac["B"])
        if pac.get("C") is not None: C_epochs.append(pac["C"])

    anova_result = None
    anova_groups = {"A_RNN": A_epochs, "B_CNN": B_epochs, "C_GNN": C_epochs}
    if all(len(g) >= 3 for g in anova_groups.values()):
        f_stat, p_val = stats.f_oneway(A_epochs, B_epochs, C_epochs)
        anova_result = {
            "F":       round(float(f_stat), 4),
            "p":       round(float(p_val),  6),
            "alpha":   ANOVA_ALPHA,
            "pass":    int(p_val > ANOVA_ALPHA),
            "verdict": "no significant arch difference" if p_val > ANOVA_ALPHA
                       else "significant arch difference (P4 FALSIFIED)",
        }

    # ── 2. Per-agent final type participation (from manifest final_metrics) ──
    agent_query_rates:   dict[str, list[float]] = {"A": [], "B": [], "C": []}
    agent_respond_rates: dict[str, list[float]] = {"A": [], "B": [], "C": []}

    for m in manifests:
        pat = (m.get("final_metrics") or {}).get("per_agent_types") or {}
        for agent in ("A", "B", "C"):
            ad = pat.get(agent) or {}
            q = ad.get("QUERY",   None)
            r = ad.get("RESPOND", None)
            if q is not None: agent_query_rates[agent].append(q)
            if r is not None: agent_respond_rates[agent].append(r)

    # ── 3. Summary statistics ──────────────────────────────────────────────
    import statistics as st

    def safe_mean(lst):  return round(st.mean(lst), 2)   if lst else None
    def safe_stdev(lst): return round(st.stdev(lst), 2)  if len(lst) > 1 else None
    def safe_median(lst):return round(st.median(lst), 2) if lst else None

    crystallised_count = sum(
        1 for m in manifests if m.get("crystallization_epoch") is not None
    )

    per_agent_summary = {}
    for agent, label in [("A", "RNN"), ("B", "CNN"), ("C", "GNN")]:
        epochs_list = anova_groups[f"{agent}_{label}"]
        q_rates = agent_query_rates[agent]
        r_rates = agent_respond_rates[agent]
        per_agent_summary[f"Agent_{agent}_{label}"] = {
            "n_crystallised": len(epochs_list),
            "mean_convergence_epoch": safe_mean(epochs_list),
            "stdev_convergence_epoch": safe_stdev(epochs_list),
            "median_convergence_epoch": safe_median(epochs_list),
            "convergence_epochs": sorted(epochs_list),
            "mean_final_query_rate":  safe_mean(q_rates),
            "mean_final_respond_rate": safe_mean(r_rates),
        }

    return {
        "n_seeds": len(manifests),
        "n_crystallised_global": crystallised_count,
        "anova": anova_result,
        "per_agent": per_agent_summary,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preregistration P4: Substrate Independence"
    )
    parser.add_argument("--seed", type=int, default=None,
                        help="Single seed (use --seeds for a list)")
    parser.add_argument("--seeds", type=int, nargs="+", default=None,
                        help="Explicit seed list, e.g. --seeds 0 1 8 10 12")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--epochs",   type=int, default=EPOCHS)
    parser.add_argument("--episodes", type=int, default=EPISODES)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Skip runs, re-run analysis on existing manifests")
    args = parser.parse_args()

    seeds = args.seeds if args.seeds else ([args.seed] if args.seed is not None else SEEDS)

    backend_dir = Path(__file__).parent
    base_output = (
        Path(args.output_dir) if args.output_dir
        else backend_dir.parent / "data" / "p4_substrate"
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

    print(f"\n{'=' * 60}")
    print(f"  Preregistration P4: Substrate Independence")
    print(f"{'=' * 60}")
    print(f"  Seeds          : {seeds[0]}-{seeds[-1]} ({len(seeds)} runs)")
    print(f"  Condition      : Protocol 1, q={QUERY_COST}x (baseline)")
    print(f"  Epochs/episodes: {args.epochs} / {args.episodes}")
    print(f"  ANOVA alpha    : {ANOVA_ALPHA} (pass: p > {ANOVA_ALPHA})")
    print(f"  Workers        : {workers}")
    print(f"  Output         : {base_output}")
    print("=" * 60 + "\n")

    if args.dry_run:
        for spec in specs:
            cmd = [sys.executable, "-u", "-m", "simulation.engine",
                   "--seed", str(spec["seed"]), "--epochs", str(spec["epochs"]),
                   "--protocol", "1", "--query-cost", "1.5", "--output-dir",
                   spec["output_dir"]]
            print(" ".join(cmd))
        return

    if not args.analyze_only:
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

                pac  = result.get("per_agent_crystallization", {})
                icon = "OK" if result["status"] == "ok" else "!!"
                print(
                    f"  {icon} seed={result['seed']:02d}"
                    f"  A={str(pac.get('A')):>4s}"
                    f"  B={str(pac.get('B')):>4s}"
                    f"  C={str(pac.get('C')):>4s}"
                    f"  (global={str(result.get('crystallization_epoch')):>4s})"
                    f"  {result['elapsed_s']:6.1f}s  {fmt_bar(done, total)}"
                )

        elapsed_total = time.time() - campaign_start
        print(f"\n  Runs complete: {done - failed}/{total}  "
              f"({elapsed_total / 60:.1f} min)\n")

    # ── Analysis ──────────────────────────────────────────────────────────────
    print("  Running P4 analysis...")
    analysis = run_analysis(base_output, seeds)

    anova = analysis.get("anova") or {}
    pa    = analysis.get("per_agent", {})

    print()
    print(f"  Per-agent convergence epochs (first 5-streak H_agent < 1.2 bits):")
    for key, vals in pa.items():
        n    = vals["n_crystallised"]
        mean = vals["mean_convergence_epoch"]
        sd   = vals["stdev_convergence_epoch"]
        med  = vals["median_convergence_epoch"]
        print(f"    {key:14s}: n={n:2d}  mean={str(mean):>6s}  "
              f"sd={str(sd):>6s}  median={str(med):>6s}")

    print()
    if anova:
        verdict = "PASS" if anova["pass"] else "FAIL"
        print(f"  ANOVA: F={anova['F']:.4f}  p={anova['p']:.6f}  "
              f"alpha={anova['alpha']}  -> {verdict}")
        print(f"  P4 verdict: {anova['verdict']}")
    else:
        print("  ANOVA: insufficient data (need n>=3 per group)")

    # Write summary
    summary = {
        "experiment":               "p4_substrate_independence",
        "preregistered_prediction": "P4",
        "campaign_date":            datetime.now().isoformat(),
        "seeds":                    seeds,
        "condition":                "baseline_q1.5",
        "epochs":                   args.epochs,
        "anova_alpha":              ANOVA_ALPHA,
        **analysis,
    }
    base_output.mkdir(parents=True, exist_ok=True)
    summary_path = base_output / "p4_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Summary: {summary_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
