"""Experiment 4 — Noise injection at the critical boundary.

Tests whether crystallized or near-crystallization protocols are robust to
channel noise. A true phase transition predicts smooth degradation; a brittle
one predicts sudden collapse.

Design
------
  Boundary query cost: q=1.0  (below baseline 1.5; expected ~30-50% crys
  without noise — near the transition zone).

  Also runs a "robust" condition at q=1.5 (confirmed 93% crys at n=15)
  to contrast noise sensitivity between boundary and robust regimes.

  Noise model: with probability `noise_prob`, the agent's intended message
  type (DECLARE/QUERY/RESPOND) is replaced by a uniformly random type before
  being deposited in the comm buffer and used in reward computation.
  The Gumbel-Softmax soft_type (gradient flow) is NOT corrupted — noise
  affects the channel, not the agent's learning signal.

  Conditions (regime × noise level):
    boundary_noise_0.00  (q=1.0, p=0.00)
    boundary_noise_0.10  (q=1.0, p=0.10)
    boundary_noise_0.20  (q=1.0, p=0.20)
    boundary_noise_0.30  (q=1.0, p=0.30)
    robust_noise_0.00    (q=1.5, p=0.00)
    robust_noise_0.10    (q=1.5, p=0.10)
    robust_noise_0.20    (q=1.5, p=0.20)
    robust_noise_0.30    (q=1.5, p=0.30)

  15 seeds × 8 conditions = 120 runs.

Prediction
----------
  At the boundary (q=1.0):  crystallization rate decreases monotonically with
    noise.  If the drop is abrupt (e.g. 40%→0% between p=0 and p=0.1), the
    protocol is brittle.  If gradual (40%→30%→20%→10%), it is robust.

  At the robust level (q=1.5):  some degradation is expected but full collapse
    only at high noise.  If the robust regime still collapses at p=0.10, the
    protocol is not truly robust.

Output
------
  data/exp4_noise/seed_{s:02d}_{condition}/manifest.json
  data/exp4_noise/exp4_summary.json

Usage
-----
  python run_exp4_noise.py
  python run_exp4_noise.py --workers 4
  python run_exp4_noise.py --dry-run
  python run_exp4_noise.py --analyze-only
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Parameters ─────────────────────────────────────────────────────────────────

SEEDS    = list(range(15))
EPOCHS   = 500
EPISODES = 10

DECLARE_COST = 1.0
RESPOND_COST = 0.8

CONDITIONS = [
    {"label": "boundary_noise_0.00", "query_cost": 1.0, "noise_prob": 0.00},
    {"label": "boundary_noise_0.10", "query_cost": 1.0, "noise_prob": 0.10},
    {"label": "boundary_noise_0.20", "query_cost": 1.0, "noise_prob": 0.20},
    {"label": "boundary_noise_0.30", "query_cost": 1.0, "noise_prob": 0.30},
    {"label": "robust_noise_0.00",   "query_cost": 1.5, "noise_prob": 0.00},
    {"label": "robust_noise_0.10",   "query_cost": 1.5, "noise_prob": 0.10},
    {"label": "robust_noise_0.20",   "query_cost": 1.5, "noise_prob": 0.20},
    {"label": "robust_noise_0.30",   "query_cost": 1.5, "noise_prob": 0.30},
]

DATA_ROOT = Path(__file__).parent.parent / "data" / "exp4_noise"


# ── Worker ─────────────────────────────────────────────────────────────────────

def _run_one(spec: dict) -> dict:
    """Run one seed under one condition (with channel noise). Called in subprocess."""
    import sys, os, random as _random
    sys.path.insert(0, os.path.dirname(__file__))
    from simulation.engine import SimulationEngine, SimulationConfig

    seed       = spec["seed"]
    noise_prob = spec["noise_prob"]
    out_dir    = spec["output_dir"]

    config = SimulationConfig(
        seed=seed,
        num_epochs=EPOCHS,
        episodes_per_epoch=EPISODES,
        protocol=1,
        declare_cost=DECLARE_COST,
        query_cost=spec["query_cost"],
        respond_cost=RESPOND_COST,
        output_dir=out_dir,
    )
    engine = SimulationEngine(config=config)

    if noise_prob > 0.0:
        # Monkey-patch protocol.resolve_signal_type to inject channel noise.
        # Only hard_type (the "transmitted" type) is corrupted.
        # soft_type (Gumbel-Softmax output, used for gradient flow) is unchanged.
        original_resolve = engine.protocol.resolve_signal_type
        rng = _random.Random(seed + 999_999)   # deterministic per-seed noise

        def noisy_resolve(type_logits, tau, training=True):
            soft_type, hard_type = original_resolve(type_logits, tau, training=training)
            if rng.random() < noise_prob:
                hard_type = rng.randint(0, 2)   # 0=DECLARE 1=QUERY 2=RESPOND
            return soft_type, hard_type

        engine.protocol.resolve_signal_type = noisy_resolve

    engine.run()
    return {"seed": seed, "condition": spec["label"]}


# ── Data loading ───────────────────────────────────────────────────────────────

def _load_manifest(path: Path) -> dict | None:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _extract(manifest: dict) -> dict:
    fm = manifest.get("final_metrics", manifest)
    return {
        "crystallized":      manifest.get("crystallized", fm.get("crystallized")),
        "crys_epoch":        manifest.get("crystallization_epoch",
                                          fm.get("crystallization_epoch")),
        "type_entropy":      fm.get("type_entropy"),
        "qrc":               fm.get("query_response_coupling"),
        "query_rate":        fm.get("query_rate"),
        "survival_rate":     fm.get("survival_rate"),
    }


# ── Campaign runner ─────────────────────────────────────────────────────────────

def run_campaign(seeds: list[int], workers: int, dry_run: bool) -> None:
    jobs = []
    for cond in CONDITIONS:
        for seed in seeds:
            out_dir = DATA_ROOT / f"seed_{seed:02d}_{cond['label']}"
            manifest_path = out_dir / "manifest.json"
            if manifest_path.exists():
                continue    # already done
            if not dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
            jobs.append({
                "seed":       seed,
                "condition":  cond["label"],
                "query_cost": cond["query_cost"],
                "noise_prob": cond["noise_prob"],
                "output_dir": str(out_dir),
            })

    if not jobs:
        print("  No new jobs (all data present).")
        return

    print(f"\n  Running {len(jobs)} jobs  (workers={workers})")
    if dry_run:
        for j in jobs[:8]:
            print(f"  DRY-RUN: {j['condition']}  seed={j['seed']}")
        if len(jobs) > 8:
            print(f"  ... ({len(jobs)-8} more)")
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
            "query_cost":         cond["query_cost"],
            "noise_prob":         cond["noise_prob"],
            "n":                  n,
            "n_crystallized":     n_crys,
            "crystallization_rate": round(n_crys / n, 4) if n else None,
            "mean_type_entropy":  _mean([r["type_entropy"] for r in rows]),
            "mean_qrc":           _mean([r["qrc"] for r in rows]),
            "mean_query_rate":    _mean([r["query_rate"] for r in rows]),
            "mean_survival_rate": _mean([r["survival_rate"] for r in rows]),
            "mean_crys_epoch":    _mean([r["crys_epoch"] for r in rows
                                         if r.get("crystallized") and r["crys_epoch"]]),
        }

    # Monotonicity check: does crys_rate decrease with noise?
    monotonicity = {}
    for regime in ("boundary", "robust"):
        vals = []
        for cond in CONDITIONS:
            if cond["label"].startswith(regime):
                cs = condition_stats[cond["label"]]
                vals.append((cond["noise_prob"], cs["crystallization_rate"] or 0.0))
        vals.sort()
        # Check pairwise monotone descent
        monotone = all(vals[i][1] >= vals[i+1][1] for i in range(len(vals)-1))
        monotonicity[regime] = {
            "rates_by_noise": vals,
            "monotone_descent": monotone,
        }

    return {
        "experiment":    "4",
        "description":   "Noise injection at critical boundary",
        "generated":     datetime.now().isoformat(),
        "n_seeds":       len(seeds),
        "conditions":    condition_stats,
        "monotonicity":  monotonicity,
    }


# ── Summary writer ─────────────────────────────────────────────────────────────

def write_summary(result: dict, out_path: Path) -> None:
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nExp 4 summary: {out_path}")

    print(f"\n  {'Condition':<30}  {'n':>3}  {'crys':>5}  {'rate':>5}  "
          f"{'H':>6}  {'QRC':>6}  {'Qrate':>6}")
    for cond in CONDITIONS:
        label = cond["label"]
        cs    = result["conditions"][label]
        n_c   = cs["n_crystallized"]
        n     = cs["n"]
        rate  = f"{cs['crystallization_rate']:.2f}" if cs["crystallization_rate"] is not None else "  N/A"
        H     = f"{cs['mean_type_entropy']:.3f}"    if cs["mean_type_entropy"]    is not None else "  N/A"
        qrc   = f"{cs['mean_qrc']:.3f}"             if cs["mean_qrc"]             is not None else "  N/A"
        qr    = f"{cs['mean_query_rate']:.3f}"      if cs["mean_query_rate"]       is not None else "  N/A"
        print(f"  {label:<30}  {n:>3}  {n_c:>5}  {rate:>5}  {H:>6}  {qrc:>6}  {qr:>6}")

    print()
    for regime in ("boundary", "robust"):
        mn = result["monotonicity"][regime]
        rates = "  ".join(f"p={p:.2f}→{r:.2f}" for p, r in mn["rates_by_noise"])
        mono  = "MONOTONE DESCENT" if mn["monotone_descent"] else "NON-MONOTONE"
        print(f"  [{regime.upper()}] {mono}:  {rates}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exp 4 -- Noise injection at critical boundary")
    parser.add_argument("--seeds",        type=int, nargs=2, default=[0, 15],
                        metavar=("START", "END"))
    parser.add_argument("--workers",      type=int, default=None)
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    args = parser.parse_args()

    seeds   = list(range(args.seeds[0], args.seeds[1]))
    workers = args.workers or max(1, (os.cpu_count() or 4) - 1)

    print(f"Exp 4 -- Noise injection  --  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]}  Workers: {workers}")
    print(f"Conditions: {len(CONDITIONS)}  x  {len(seeds)} seeds = {len(CONDITIONS)*len(seeds)} runs")
    print(f"Data: {DATA_ROOT}")

    if args.analyze_only:
        result = analyze(seeds)
        out_path = DATA_ROOT / "exp4_summary.json"
        write_summary(result, out_path)
        return

    if not args.dry_run:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)

    run_campaign(seeds, workers, args.dry_run)

    if not args.dry_run:
        result = analyze(seeds)
        out_path = DATA_ROOT / "exp4_summary.json"
        write_summary(result, out_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
