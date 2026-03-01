"""Experiment 11 — Saturation forcing and visible failure.

Forces sustained energy depletion through extreme query cost, testing whether
coordination coherence fails visibly when capacity is exceeded. Directly tests
the AnnA capacity-binding claim: coherence must fail at capacity exceedance;
if it stays "stable," there is an escape hatch (agents stop communicating to
survive, masking the failure).

Design
------
  Three phases of saturation:
    saturation_q10 : query_cost=10.0  (moderate overload)
    saturation_q20 : query_cost=20.0  (severe overload)
    saturation_q50 : query_cost=50.0  (extreme overload — expected full collapse)
    baseline_ref   : query_cost=1.5   (comparison reference)

  Protocol 1 throughout. DECLARE=1.0, RESPOND=0.8.
  Seeds: 0..14 (15 per condition = 60 runs total).
  Epochs: 500. Episodes: 10.

Key outcome measures:
  1. survival_rate: approaches 0 under saturation?
  2. query_rate: do agents stop querying to avoid energy depletion?
  3. qrc: does QRC collapse even when query rate drops?
  4. type_entropy: does protocol collapse to pure DECLARE (H→0)?
  5. crystallization_epoch: can the system crystallize under saturation?
  6. escape_hatch_detected: bool — survival remains non-trivial while
     query_rate drops below 1% (agents avoid queries to survive =
     the protocol masks failure, not genuine coherence)

Predicted signatures:
  - q=10: partial degradation. QRC reduced, survival drops, queries rarer.
  - q=20: near-collapse. Near-zero survival, QRC close to 0.
  - q=50: full collapse. Zero survival, zero QRC, pure DECLARE (H→0).
  - If survival stays high at q=20+: escape hatch detected.

Usage
-----
  python run_exp11_saturation.py
  python run_exp11_saturation.py --conditions saturation_q20 baseline_ref
  python run_exp11_saturation.py --workers 4
  python run_exp11_saturation.py --dry-run
  python run_exp11_saturation.py --analyze-only

Output
------
  data/exp11_saturation/{condition}/seed_{s:02d}/manifest.json
  data/exp11_saturation/exp11_summary.json
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

# ── Preregistered parameters ───────────────────────────────────────────────────

SEEDS        = list(range(15))
EPOCHS       = 500
EPISODES     = 10
DECLARE_COST = 1.0
RESPOND_COST = 0.8

CONDITIONS = {
    "saturation_q10": {
        "label":       "Saturation q=10 (moderate overload)",
        "query_cost":  10.0,
    },
    "saturation_q20": {
        "label":       "Saturation q=20 (severe overload)",
        "query_cost":  20.0,
    },
    "saturation_q50": {
        "label":       "Saturation q=50 (extreme overload — expected full collapse)",
        "query_cost":  50.0,
    },
    "baseline_ref": {
        "label":       "Baseline q=1.5 (reference)",
        "query_cost":  1.5,
    },
}

# Escape hatch threshold: survival is "non-trivial" (>10%) but query rate
# is near-zero (<1%) — agents preserve survival by abandoning the protocol
ESCAPE_HATCH_SURVIVAL_MIN = 0.10
ESCAPE_HATCH_QUERY_MAX    = 0.01


# ── Worker ─────────────────────────────────────────────────────────────────────

def _run_one(spec: dict) -> dict:
    """Run one seed. Called in subprocess."""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from simulation.engine import SimulationEngine, SimulationConfig

    cfg = SimulationConfig(
        seed=spec["seed"],
        num_epochs=spec["epochs"],
        episodes_per_epoch=spec["episodes"],
        protocol=1,
        declare_cost=DECLARE_COST,
        query_cost=spec["query_cost"],
        respond_cost=RESPOND_COST,
        output_dir=spec["output_dir"],
    )
    engine = SimulationEngine(config=cfg)
    engine.run()

    # Extract summary metrics from epoch_metrics
    ems = engine.epoch_metrics
    if not ems:
        return {"condition": spec["condition"], "seed": spec["seed"],
                "error": "no epoch metrics"}

    # Mean over last 100 epochs (post-adaptation window)
    window = ems[-100:]

    def _epoch_query_rate(m: dict) -> float | None:
        inq = m.get("inquiry", {})
        pat = inq.get("per_agent_types", {})
        if not pat:
            return None
        qs = [pat[a].get("QUERY", 0) for a in pat]
        return sum(qs) / len(qs) if qs else None

    def _mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 6) if xs else None

    survival_late  = _mean([m.get("survival_rate") for m in window])
    qrc_late       = _mean([m.get("inquiry", {}).get("query_response_coupling")
                             for m in window])
    entropy_late   = _mean([m.get("inquiry", {}).get("type_entropy") for m in window])
    query_rate_late = _mean([_epoch_query_rate(m) for m in window])

    # Over full run
    survival_all    = _mean([m.get("survival_rate") for m in ems])
    qrc_all         = _mean([m.get("inquiry", {}).get("query_response_coupling")
                              for m in ems])
    query_rate_all  = _mean([_epoch_query_rate(m) for m in ems])
    entropy_all     = _mean([m.get("inquiry", {}).get("type_entropy") for m in ems])

    # Crystallization
    crys_epoch = engine.epoch_metrics[-1].get("crystallization_epoch") \
                 if engine.epoch_metrics else None
    # Check manifest
    mf_path = os.path.join(spec["output_dir"], "manifest.json")
    if os.path.exists(mf_path):
        with open(mf_path) as f:
            mf = json.load(f)
        crys_epoch = mf.get("crystallization_epoch")

    # Escape hatch detection
    escape_hatch = (
        survival_late is not None and survival_late > ESCAPE_HATCH_SURVIVAL_MIN
        and query_rate_late is not None and query_rate_late < ESCAPE_HATCH_QUERY_MAX
    )

    # QRC collapse: QRC < 0.10 in last 100 epochs
    qrc_collapsed = qrc_late is not None and qrc_late < 0.10

    # Protocol collapse: entropy < 0.10 bits in last 100 epochs (near-pure DECLARE)
    protocol_collapsed = entropy_late is not None and entropy_late < 0.10

    return {
        "condition":          spec["condition"],
        "seed":               spec["seed"],
        "crystallized":       crys_epoch is not None,
        "crystallization_epoch": crys_epoch,
        # Late-window (last 100 epochs)
        "survival_rate_late": survival_late,
        "qrc_late":           qrc_late,
        "query_rate_late":    query_rate_late,
        "entropy_late":       entropy_late,
        # Full-run averages
        "survival_rate_all":  survival_all,
        "qrc_all":            qrc_all,
        "query_rate_all":     query_rate_all,
        "entropy_all":        entropy_all,
        # Diagnostic flags
        "qrc_collapsed":      qrc_collapsed,
        "protocol_collapsed": protocol_collapsed,
        "escape_hatch_detected": escape_hatch,
    }


# ── Campaign runner ────────────────────────────────────────────────────────────

def run_campaign(conditions: list[str], seeds: list[int], workers: int,
                 dry_run: bool, data_root: Path) -> list[dict]:
    jobs = []
    for cond in conditions:
        for seed in seeds:
            out_dir = data_root / cond / f"seed_{seed:02d}"
            if not dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
            jobs.append({
                "condition":  cond,
                "seed":       seed,
                "query_cost": CONDITIONS[cond]["query_cost"],
                "epochs":     EPOCHS,
                "episodes":   EPISODES,
                "output_dir": str(out_dir),
            })

    print(f"\nExp 11 -- Saturation forcing and visible failure")
    print(f"  conditions: {conditions}")
    print(f"  seeds:      {seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)")
    print(f"  total:      {len(jobs)} runs  |  workers: {workers}")
    print(f"  output:     {data_root}")

    if dry_run:
        for j in jobs[:5]:
            print(f"  DRY-RUN: {j['condition']}  seed={j['seed']}")
        if len(jobs) > 5:
            print(f"  ... ({len(jobs)-5} more)")
        return []

    results = []
    t0   = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one, j): j for j in jobs}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
                done += 1
                esc  = "ESC"  if r.get("escape_hatch_detected") else "   "
                coll = "COLL" if r.get("qrc_collapsed") else "    "
                pcol = "PCOL" if r.get("protocol_collapsed") else "    "
                surv = f"{r['survival_rate_late']:.3f}" \
                       if r.get("survival_rate_late") is not None else " None"
                qrc  = f"{r['qrc_late']:.3f}" \
                       if r.get("qrc_late") is not None else " None"
                qr   = f"{r['query_rate_late']:.3f}" \
                       if r.get("query_rate_late") is not None else " None"
                print(f"  [{done:2d}/{len(jobs)}]  {r['condition']:18s}  seed={r['seed']:02d}"
                      f"  {esc} {coll} {pcol}"
                      f"  surv={surv}  qrc={qrc}  qr={qr}")
            except Exception as e:
                j = futures[fut]
                print(f"  ERROR: {j['condition']} seed={j['seed']}: {e}")

    print(f"\nExp 11 done: {done}/{len(jobs)} runs in {time.time()-t0:.0f}s")
    return results


# ── Summary ────────────────────────────────────────────────────────────────────

def write_summary(results: list[dict], data_root: Path) -> None:
    if not results:
        return

    from collections import defaultdict
    by_cond: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_cond[r["condition"]].append(r)

    def _mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 6) if xs else None

    cond_summaries = []
    for cond in CONDITIONS:
        runs = by_cond.get(cond, [])
        if not runs:
            continue
        n = len(runs)
        cond_summaries.append({
            "condition":                cond,
            "label":                    CONDITIONS[cond]["label"],
            "query_cost":               CONDITIONS[cond]["query_cost"],
            "n_seeds":                  n,
            "crystallization_rate":     round(sum(1 for r in runs if r["crystallized"]) / n, 4),
            "mean_survival_late":       _mean([r["survival_rate_late"] for r in runs]),
            "mean_qrc_late":            _mean([r["qrc_late"] for r in runs]),
            "mean_query_rate_late":     _mean([r["query_rate_late"] for r in runs]),
            "mean_entropy_late":        _mean([r["entropy_late"] for r in runs]),
            "n_qrc_collapsed":          sum(1 for r in runs if r.get("qrc_collapsed")),
            "n_protocol_collapsed":     sum(1 for r in runs if r.get("protocol_collapsed")),
            "n_escape_hatch":           sum(1 for r in runs if r.get("escape_hatch_detected")),
        })

    summary = {
        "experiment":   "11",
        "description":  "Saturation forcing and visible failure",
        "generated":    datetime.now().isoformat(),
        "n_seeds":      len(SEEDS),
        "conditions":   cond_summaries,
        "per_seed":     sorted(results, key=lambda r: (r["condition"], r["seed"])),
    }

    out = data_root / "exp11_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nExp 11 summary: {out}")

    print(f"\n  {'condition':20s}  {'q_cost':>6}  {'survival':>8}  "
          f"{'qrc':>6}  {'q_rate':>7}  {'entropy':>7}  "
          f"{'QRC_coll':>8}  {'Pcol':>4}  {'Esc':>3}")
    for c in cond_summaries:
        def _fmt(v): return f"{v:.4f}" if v is not None else "  None"
        print(f"  {c['condition']:20s}  {c['query_cost']:>6.1f}  "
              f"{_fmt(c['mean_survival_late']):>8}  "
              f"{_fmt(c['mean_qrc_late']):>6}  "
              f"{_fmt(c['mean_query_rate_late']):>7}  "
              f"{_fmt(c['mean_entropy_late']):>7}  "
              f"{c['n_qrc_collapsed']:>8d}/{c['n_seeds']}  "
              f"{c['n_protocol_collapsed']:>2d}/{c['n_seeds']}  "
              f"{c['n_escape_hatch']:>2d}/{c['n_seeds']}")


# ── Analyze-only ───────────────────────────────────────────────────────────────

def analyze_only(conditions: list[str], seeds: list[int], data_root: Path) -> None:
    results = []
    for cond in conditions:
        for seed in seeds:
            p = data_root / cond / f"seed_{seed:02d}" / "manifest.json"
            if not p.exists():
                print(f"  WARNING: missing {p}")
                continue
            with open(p) as f:
                mf = json.load(f)
            fm = mf.get("final_metrics", {})
            pat = fm.get("per_agent_types", {})
            q_rate = None
            if pat:
                qs = [pat[a].get("QUERY", 0) for a in pat]
                q_rate = round(sum(qs) / len(qs), 6) if qs else None
            surv = fm.get("survival_rate")
            escape = (surv is not None and surv > ESCAPE_HATCH_SURVIVAL_MIN
                      and q_rate is not None and q_rate < ESCAPE_HATCH_QUERY_MAX)
            qrc_v = fm.get("qrc")
            results.append({
                "condition":          cond,
                "seed":               seed,
                "crystallized":       mf.get("crystallization_epoch") is not None,
                "crystallization_epoch": mf.get("crystallization_epoch"),
                "survival_rate_late": surv,
                "qrc_late":           qrc_v,
                "query_rate_late":    q_rate,
                "entropy_late":       fm.get("type_entropy"),
                "survival_rate_all":  surv,
                "qrc_all":            qrc_v,
                "query_rate_all":     q_rate,
                "entropy_all":        fm.get("type_entropy"),
                "qrc_collapsed":      qrc_v is not None and qrc_v < 0.10,
                "protocol_collapsed": fm.get("type_entropy") is not None
                                      and fm.get("type_entropy") < 0.10,
                "escape_hatch_detected": escape,
            })
    if results:
        write_summary(results, data_root)
    else:
        print("  No data found.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exp 11 -- Saturation forcing and visible failure")
    parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS.keys()),
                        choices=list(CONDITIONS.keys()))
    parser.add_argument("--seeds",       type=int, nargs=2, default=[0, 15],
                        metavar=("START", "END"))
    parser.add_argument("--workers",     type=int, default=None)
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--data-dir",    type=str,
                        default=str(Path(__file__).parent.parent / "data" / "exp11_saturation"))
    args = parser.parse_args()

    seeds     = list(range(args.seeds[0], args.seeds[1]))
    workers   = args.workers or max(1, (os.cpu_count() or 4) - 1)
    data_root = Path(args.data_dir)

    print(f"Exp 11 -- Saturation  --  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]}  Workers: {workers}  Data: {data_root}")

    if args.analyze_only:
        analyze_only(args.conditions, seeds, data_root)
        return

    if not args.dry_run:
        data_root.mkdir(parents=True, exist_ok=True)

    results = run_campaign(args.conditions, seeds, workers, args.dry_run, data_root)
    if results:
        write_summary(results, data_root)
    print("\nDone.")


if __name__ == "__main__":
    main()
