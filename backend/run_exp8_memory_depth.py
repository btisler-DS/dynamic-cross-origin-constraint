"""Experiment 8 — Memory depth scaling test (Barenholtz claim).

Tests whether a minimum recurrent memory depth exists for stable protocol
crystallization. Sweeps the GRU hidden_dim across 5 levels, measuring
whether emergence probability increases with depth and whether there is a
sharp knee point below which crystallization fails.

Architecture note
-----------------
  hidden_dim controls all three agents simultaneously:
    - Agent A (RNN/GRU): GRUCell(hidden_dim*2, hidden_dim) — directly sets
      recurrent memory size.
    - Agent B (CNN): spatial_encoder output size.
    - Agent C (GNN): attention head size.

  The primary variable of interest is Agent A's GRU depth. Agents B and C
  scale proportionally, which is a limitation noted in the results.

Conditions
----------
  depth_4   (hidden_dim=4)
  depth_8   (hidden_dim=8)
  depth_16  (hidden_dim=16)
  depth_32  (hidden_dim=32)
  depth_64  (hidden_dim=64, baseline — matches all confirmatory campaign runs)

  15 seeds × 5 conditions = 75 runs.

Prediction (Barenholtz claim, Exp 8)
-------------------------------------
  A knee point exists: below it (hidden_dim < threshold), crystallization
  probability is near 0; above it, crystallization rate rises sharply.
  This would be evidence that minimum memory depth is necessary for stable
  protocol formation, as predicted by the theory.

Output
------
  data/exp8_memory_depth/seed_{s:02d}_{condition}/manifest.json
  data/exp8_memory_depth/exp8_summary.json

Usage
-----
  python run_exp8_memory_depth.py
  python run_exp8_memory_depth.py --workers 4
  python run_exp8_memory_depth.py --dry-run
  python run_exp8_memory_depth.py --analyze-only
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

# ── Parameters ─────────────────────────────────────────────────────────────────

SEEDS        = list(range(15))
EPOCHS       = 500
EPISODES     = 10
DECLARE_COST = 1.0
QUERY_COST   = 1.5   # baseline query cost (same as all confirmatory runs)
RESPOND_COST = 0.8

CONDITIONS = [
    {"label": "depth_4",  "hidden_dim": 4},
    {"label": "depth_8",  "hidden_dim": 8},
    {"label": "depth_16", "hidden_dim": 16},
    {"label": "depth_32", "hidden_dim": 32},
    {"label": "depth_64", "hidden_dim": 64},   # baseline
]

DATA_ROOT = Path(__file__).parent.parent / "data" / "exp8_memory_depth"


# ── Worker ─────────────────────────────────────────────────────────────────────

def _run_one(spec: dict) -> dict:
    """Run one seed under one memory depth condition. Called in subprocess."""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from simulation.engine import SimulationEngine, SimulationConfig

    config = SimulationConfig(
        seed=spec["seed"],
        num_epochs=EPOCHS,
        episodes_per_epoch=EPISODES,
        protocol=1,
        declare_cost=DECLARE_COST,
        query_cost=QUERY_COST,
        respond_cost=RESPOND_COST,
        hidden_dim=spec["hidden_dim"],
        output_dir=spec["output_dir"],
    )
    engine = SimulationEngine(config=config)
    engine.run()
    return {"seed": spec["seed"], "condition": spec["label"]}


# ── Data loading ───────────────────────────────────────────────────────────────

def _load_manifest(path: Path) -> dict | None:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _extract(manifest: dict) -> dict:
    fm = manifest.get("final_metrics", manifest)
    return {
        "crystallized":   manifest.get("crystallized", fm.get("crystallized")),
        "crys_epoch":     manifest.get("crystallization_epoch",
                                       fm.get("crystallization_epoch")),
        "type_entropy":   fm.get("type_entropy"),
        "qrc":            fm.get("query_response_coupling"),
        "query_rate":     fm.get("query_rate"),
        "survival_rate":  fm.get("survival_rate"),
    }


# ── Campaign runner ─────────────────────────────────────────────────────────────

def run_campaign(seeds: list[int], workers: int, dry_run: bool) -> None:
    jobs = []
    for cond in CONDITIONS:
        for seed in seeds:
            out_dir = DATA_ROOT / f"seed_{seed:02d}_{cond['label']}"
            if (out_dir / "manifest.json").exists():
                continue
            if not dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
            jobs.append({
                "seed":       seed,
                "condition":  cond["label"],
                "hidden_dim": cond["hidden_dim"],
                "output_dir": str(out_dir),
            })

    if not jobs:
        print("  No new jobs (all data present).")
        return

    print(f"\n  Running {len(jobs)} jobs  (workers={workers})")
    if dry_run:
        for j in jobs[:5]:
            print(f"  DRY-RUN: {j['condition']}  seed={j['seed']}")
        if len(jobs) > 5:
            print(f"  ... ({len(jobs)-5} more)")
        return

    t0 = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one, j): j for j in jobs}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                done += 1
                print(f"  [{done:3d}/{len(jobs)}]  {r['condition']}  seed={r['seed']:02d}")
            except Exception as e:
                j = futures[fut]
                print(f"  ERROR: {j['condition']}  seed={j['seed']}: {e}")
    print(f"  Done in {time.time()-t0:.0f}s")


# ── Analysis ───────────────────────────────────────────────────────────────────

def analyze(seeds: list[int]) -> dict:
    per_condition: dict[str, list[dict]] = {c["label"]: [] for c in CONDITIONS}

    for cond in CONDITIONS:
        for seed in seeds:
            out_dir = DATA_ROOT / f"seed_{seed:02d}_{cond['label']}"
            m = _load_manifest(out_dir / "manifest.json")
            if m is None:
                continue
            d = _extract(m)
            d["seed"] = seed
            d["condition"] = cond["label"]
            per_condition[cond["label"]].append(d)

    def _mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 4) if xs else None

    condition_stats = {}
    for cond in CONDITIONS:
        label = cond["label"]
        rows  = per_condition[label]
        n     = len(rows)
        n_crys = sum(1 for r in rows if r.get("crystallized"))
        condition_stats[label] = {
            "hidden_dim":          cond["hidden_dim"],
            "n":                   n,
            "n_crystallized":      n_crys,
            "crystallization_rate": round(n_crys / n, 4) if n else None,
            "mean_type_entropy":   _mean([r["type_entropy"] for r in rows]),
            "mean_qrc":            _mean([r["qrc"] for r in rows]),
            "mean_query_rate":     _mean([r["query_rate"] for r in rows]),
            "mean_survival_rate":  _mean([r["survival_rate"] for r in rows]),
            "mean_crys_epoch":     _mean([r["crys_epoch"] for r in rows
                                          if r.get("crystallized") and r["crys_epoch"]]),
        }

    # Knee detection: look for the largest pairwise gap in crys_rate as depth increases
    depth_rates = [
        (cond["hidden_dim"], condition_stats[cond["label"]]["crystallization_rate"] or 0.0)
        for cond in CONDITIONS
    ]
    depth_rates.sort()
    gaps = [(depth_rates[i+1][0], depth_rates[i+1][1] - depth_rates[i][1])
            for i in range(len(depth_rates)-1)]
    knee_above = max(gaps, key=lambda x: x[1]) if gaps else None

    return {
        "experiment":   "8",
        "description":  "Memory depth scaling (Barenholtz claim)",
        "generated":    datetime.now().isoformat(),
        "n_seeds":      len(seeds),
        "query_cost":   QUERY_COST,
        "conditions":   condition_stats,
        "depth_rates":  depth_rates,
        "knee_analysis": {
            "gaps":              gaps,
            "largest_gap_above_depth": knee_above[0] if knee_above else None,
            "largest_gap_size":        round(knee_above[1], 4) if knee_above else None,
        },
    }


# ── Summary writer ─────────────────────────────────────────────────────────────

def write_summary(result: dict, out_path: Path) -> None:
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nExp 8 summary: {out_path}")

    print(f"\n  {'Condition':<12}  {'dim':>4}  {'n':>3}  {'crys':>5}  "
          f"{'rate':>5}  {'H':>6}  {'QRC':>6}  {'mean_epoch':>10}")
    for cond in CONDITIONS:
        label = cond["label"]
        cs    = result["conditions"][label]
        n_c   = cs["n_crystallized"]
        n     = cs["n"]
        rate  = f"{cs['crystallization_rate']:.2f}" if cs["crystallization_rate"] is not None else " N/A"
        H     = f"{cs['mean_type_entropy']:.3f}"    if cs["mean_type_entropy"]    is not None else " N/A"
        qrc   = f"{cs['mean_qrc']:.3f}"             if cs["mean_qrc"]             is not None else " N/A"
        me    = f"{cs['mean_crys_epoch']:.0f}"      if cs["mean_crys_epoch"]      is not None else " N/A"
        print(f"  {label:<12}  {cond['hidden_dim']:>4}  {n:>3}  {n_c:>5}  "
              f"{rate:>5}  {H:>6}  {qrc:>6}  {me:>10}")

    ka = result["knee_analysis"]
    if ka["largest_gap_above_depth"] is not None:
        print(f"\n  Knee point: largest crys_rate gain at depth {ka['largest_gap_above_depth']}"
              f"  (gap = {ka['largest_gap_size']:.3f})")
    print(f"\n  Rate by depth: " +
          "  ".join(f"dim={d}→{r:.2f}" for d, r in result["depth_rates"]))


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exp 8 -- Memory depth scaling (Barenholtz claim)")
    parser.add_argument("--seeds",        type=int, nargs=2, default=[0, 15],
                        metavar=("START", "END"))
    parser.add_argument("--workers",      type=int, default=None)
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    args = parser.parse_args()

    seeds   = list(range(args.seeds[0], args.seeds[1]))
    workers = args.workers or max(1, (os.cpu_count() or 4) - 1)

    print(f"Exp 8 -- Memory depth scaling  --  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]}  Workers: {workers}")
    print(f"Conditions: {len(CONDITIONS)}  x  {len(seeds)} seeds = {len(CONDITIONS)*len(seeds)} runs")
    print(f"Data: {DATA_ROOT}")

    if args.analyze_only:
        result = analyze(seeds)
        write_summary(result, DATA_ROOT / "exp8_summary.json")
        return

    if not args.dry_run:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)

    run_campaign(seeds, workers, args.dry_run)

    if not args.dry_run:
        result = analyze(seeds)
        write_summary(result, DATA_ROOT / "exp8_summary.json")

    print("\nDone.")


if __name__ == "__main__":
    main()
