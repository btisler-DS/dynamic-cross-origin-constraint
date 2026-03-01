"""P2 Cost-Sensitivity rerun -- actual query rates via per_agent_types.

The original campaign manifests predate the per_agent_types field in the engine.
This rerun executes the three non-baseline cost conditions (low_pressure,
high_pressure, extreme) with the current engine, which saves per_agent_types
to final_metrics, enabling a proper Pearson r test with actual query rates.

The baseline condition (Protocol 1, q=1.5) is already available from the P4
substrate v2 run (data/p4_substrate_v2/), which has per_agent_types for all
15 seeds. Those data are loaded here alongside the new runs.

Conditions re-run
-----------------
  low_pressure  : Protocol 1, DECLARE=1.0x, QUERY=1.2x, RESPOND=0.9x
  high_pressure : Protocol 1, DECLARE=1.0x, QUERY=3.0x, RESPOND=0.5x
  extreme       : Protocol 1, DECLARE=1.0x, QUERY=5.0x, RESPOND=0.3x

Control and baseline are NOT re-run (control has no QUERY type, irrelevant;
baseline is already available from P4 v2).

Output
------
  data/p2_rerun/{condition}/seed_{:02d}/manifest.json
  data/p2_rerun/p2_summary.json

Usage
-----
  python run_p2_rerun.py [--seeds 0..14] [--epochs 500] [--workers 5]
  python run_p2_rerun.py --analyze-only
  python run_p2_rerun.py --conditions low_pressure high_pressure
"""

from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

SEEDS    = list(range(15))
EPOCHS   = 500
EPISODES = 10
PROTOCOL = 1

CONDITIONS: dict[str, dict] = {
    "low_pressure": {
        "declare_cost": 1.0,
        "query_cost":   1.2,
        "respond_cost": 0.9,
        "label":        "Low pressure (q=1.2)",
    },
    "high_pressure": {
        "declare_cost": 1.0,
        "query_cost":   3.0,
        "respond_cost": 0.5,
        "label":        "High pressure (q=3.0)",
    },
    "extreme": {
        "declare_cost": 1.0,
        "query_cost":   5.0,
        "respond_cost": 0.3,
        "label":        "Extreme (q=5.0)",
    },
}

# Baseline is loaded from P4 substrate v2, not re-run
BASELINE_COST = 1.5
P4_DIR   = Path(__file__).parent.parent / "data" / "p4_substrate_v2"

# ── Worker ────────────────────────────────────────────────────────────────────

def run_one(spec: dict) -> dict:
    import sys, os, time
    sys.path.insert(0, os.path.dirname(__file__))
    from simulation.engine import SimulationEngine, SimulationConfig

    t0  = time.time()
    cfg = SimulationConfig(
        seed=spec["seed"],
        num_epochs=spec["epochs"],
        episodes_per_epoch=spec["episodes"],
        protocol=PROTOCOL,
        declare_cost=spec["declare_cost"],
        query_cost=spec["query_cost"],
        respond_cost=spec["respond_cost"],
        output_dir=spec["output_dir"],
    )
    engine = SimulationEngine(config=cfg)
    engine.run()

    mf_path = os.path.join(spec["output_dir"], "manifest.json")
    manifest = {}
    if os.path.exists(mf_path):
        with open(mf_path) as f:
            manifest = json.load(f)

    fm  = manifest.get("final_metrics", {})
    pat = fm.get("per_agent_types")
    q_rate = None
    if pat:
        q_rate = round((pat["A"]["QUERY"] + pat["B"]["QUERY"] + pat["C"]["QUERY"]) / 3.0, 4)

    return {
        "condition":   spec["condition"],
        "seed":        spec["seed"],
        "status":      "ok",
        "elapsed_s":   round(time.time() - t0, 1),
        "crys_epoch":  manifest.get("crystallization_epoch"),
        "q_rate":      q_rate,
        "qrc":         fm.get("qrc"),
    }


# ── Analysis ──────────────────────────────────────────────────────────────────

def _load_manifest(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_baseline_query_rates() -> list[float]:
    """Load per_agent_types from P4 substrate v2 (baseline condition, n=15)."""
    rates = []
    for seed_dir in sorted(P4_DIR.iterdir()):
        if not seed_dir.is_dir():
            continue
        mf = _load_manifest(seed_dir / "manifest.json")
        fm = mf.get("final_metrics", {})
        pat = fm.get("per_agent_types")
        if pat:
            q = (pat["A"]["QUERY"] + pat["B"]["QUERY"] + pat["C"]["QUERY"]) / 3.0
            rates.append(round(q, 4))
    return rates


def run_analysis(base_output: Path, seeds: list[int], cond_keys: list[str]) -> dict:
    import statistics as st
    from scipy.stats import pearsonr

    cost_vec:  list[float] = []
    q_vec:     list[float] = []
    cond_data: dict        = {}

    # Load baseline from P4 v2
    baseline_rates = _load_baseline_query_rates()
    if baseline_rates:
        for q in baseline_rates:
            cost_vec.append(BASELINE_COST)
            q_vec.append(q)
        cond_data["baseline"] = {
            "cost":       BASELINE_COST,
            "label":      "Baseline (q=1.5) [from P4 v2]",
            "n":          len(baseline_rates),
            "mean_q_rate": round(st.mean(baseline_rates), 4),
            "sd_q_rate":   round(st.stdev(baseline_rates), 4),
        }

    # Load re-run conditions
    for cond_key in cond_keys:
        info  = CONDITIONS[cond_key]
        cost  = info["query_cost"]
        rates = []
        for seed in seeds:
            seed_dir = base_output / cond_key / f"seed_{seed:02d}"
            mf = _load_manifest(seed_dir / "manifest.json")
            if not mf:
                continue
            fm  = mf.get("final_metrics", {})
            pat = fm.get("per_agent_types")
            if pat:
                q = (pat["A"]["QUERY"] + pat["B"]["QUERY"] + pat["C"]["QUERY"]) / 3.0
                rates.append(round(q, 4))
                cost_vec.append(cost)
                q_vec.append(q)

        if rates:
            cond_data[cond_key] = {
                "cost":        cost,
                "label":       info["label"],
                "n":           len(rates),
                "mean_q_rate": round(st.mean(rates), 4),
                "sd_q_rate":   round(st.stdev(rates), 4) if len(rates) > 1 else None,
            }

    # Pearson r
    r_result = p_result = None
    if len(cost_vec) >= 4:
        r_result, p_result = pearsonr(cost_vec, q_vec)
        r_result = round(float(r_result), 4)
        p_result = float(p_result)

    verdict = "NOT COMPUTED"
    if r_result is not None:
        if r_result < -0.70 and p_result < 0.01:
            verdict = "CONFIRMED"
        elif r_result < -0.70:
            verdict = "NOT CONFIRMED (p >= 0.01)"
        elif p_result < 0.01:
            verdict = "NOT CONFIRMED (r >= -0.70)"
        else:
            verdict = "NOT CONFIRMED"

    return {
        "conditions":  cond_data,
        "n_total":     len(cost_vec),
        "r":           r_result,
        "p_twotail":   round(p_result, 10) if p_result is not None else None,
        "p_onetail":   round(p_result / 2, 10) if p_result is not None and r_result and r_result < 0 else None,
        "r_threshold": -0.70,
        "alpha":       0.01,
        "pass":        int(r_result is not None and r_result < -0.70 and p_result < 0.01),
        "verdict":     verdict,
    }


# ── Progress bar ──────────────────────────────────────────────────────────────

def fmt_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / max(total, 1))
    return "[" + "#" * filled + "." * (width - filled) + "]"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="P2 cost-sensitivity rerun with actual query rates")
    parser.add_argument("--seeds",        type=int, nargs="+", default=None)
    parser.add_argument("--epochs",       type=int, default=EPOCHS)
    parser.add_argument("--episodes",     type=int, default=EPISODES)
    parser.add_argument("--workers",      type=int, default=None)
    parser.add_argument("--output-dir",   type=str, default=None)
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--conditions",   type=str, nargs="+", default=None,
                        help="Subset: low_pressure high_pressure extreme")
    args = parser.parse_args()

    seeds      = args.seeds if args.seeds else SEEDS
    cond_keys  = args.conditions if args.conditions else list(CONDITIONS)
    backend    = Path(__file__).parent
    base_out   = (Path(args.output_dir) if args.output_dir
                  else backend.parent / "data" / "p2_rerun")
    cpu        = os.cpu_count() or 2
    workers    = args.workers if args.workers else max(1, cpu - 1)

    print(f"\n{'=' * 60}")
    print(f"  P2 Cost-Sensitivity Rerun -- Actual Query Rates")
    print(f"{'=' * 60}")
    print(f"  Conditions : {cond_keys}")
    print(f"  Seeds      : {seeds}")
    print(f"  Epochs     : {args.epochs}  Episodes: {args.episodes}")
    print(f"  Workers    : {workers}")
    print(f"  Output     : {base_out}")
    print("=" * 60 + "\n")

    if not args.analyze_only:
        specs = [
            {
                "condition":   cond_key,
                "seed":        seed,
                "output_dir":  str(base_out / cond_key / f"seed_{seed:02d}"),
                "epochs":      args.epochs,
                "episodes":    args.episodes,
                "declare_cost": CONDITIONS[cond_key]["declare_cost"],
                "query_cost":   CONDITIONS[cond_key]["query_cost"],
                "respond_cost": CONDITIONS[cond_key]["respond_cost"],
            }
            for cond_key in cond_keys
            for seed in seeds
        ]
        total  = len(specs)
        done_n = 0
        t_camp = time.time()

        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_one, s): s for s in specs}
            for future in as_completed(futures):
                result  = future.result()
                done_n += 1
                q_str   = f"q_rate={result['q_rate']:.3f}" if result["q_rate"] is not None else "q_rate=N/A"
                print(
                    f"  OK [{result['condition']:14s}] seed={result['seed']:02d}"
                    f"  {q_str}  {result['elapsed_s']:7.1f}s"
                    f"  {fmt_bar(done_n, total)}"
                )

        elapsed = time.time() - t_camp
        print(f"\n  Runs complete: {done_n}/{total}  ({elapsed / 60:.1f} min)\n")

    # Analysis
    print("  Running P2 analysis with actual query rates...\n")
    result = run_analysis(base_out, seeds, cond_keys)

    # Print per-condition table
    print(f"  {'Condition':<16} {'cost':>6} {'n':>4} {'mean_Q':>8} {'sd_Q':>8}")
    print("  " + "-" * 46)
    for cond, cs in result["conditions"].items():
        sd_str = f"{cs['sd_q_rate']:.4f}" if cs.get("sd_q_rate") is not None else "  N/A"
        print(f"  {cond:<16} {cs['cost']:>6.1f} {cs['n']:>4d} "
              f"{cs['mean_q_rate']:>8.4f} {sd_str:>8}")

    print()
    r   = result.get("r")
    p2  = result.get("p_twotail")
    p1  = result.get("p_onetail")
    r_s  = f"{r}"   if r  is not None else "N/A"
    p2_s = f"{p2:.2e}" if p2 is not None else "N/A"
    p1_s = f"{p1:.2e}" if p1 is not None else "N/A"
    print(f"  n_total={result['n_total']}  r={r_s}  p(2-tail)={p2_s}  p(1-tail)={p1_s}")
    print(f"  r_threshold={result['r_threshold']}  alpha={result['alpha']}")
    print(f"  Verdict: {result['verdict']}")
    if result.get("pass"):
        print("  P2 CONFIRMED with actual query rates.")
    else:
        print("  P2 NOT CONFIRMED with actual query rates.")

    # Write summary
    summary = {
        "experiment":    "p2_cost_sensitivity_rerun",
        "analysis_date": datetime.now().isoformat(),
        "note":          ("Baseline from P4 substrate v2 (data/p4_substrate_v2/); "
                          "other conditions re-run with current engine."),
        **result,
    }
    base_out.mkdir(parents=True, exist_ok=True)
    out_path = base_out / "p2_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Summary: {out_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
