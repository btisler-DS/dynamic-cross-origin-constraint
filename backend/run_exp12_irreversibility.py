"""Experiment 12 — Irreversibility test.

Overloads a crystallized system until protocol breaks down, then restores
resources to pre-overload levels. Tests whether loss is irreversible:
does recovery fully restore the prior protocol, or does permanent drift remain?

Permanent drift = history-bearing structure (the weights retain a scar from
the overload that prevents full return to the crystallized state).

Design — three-phase per seed:
  Phase 1 — Crystallization (200 epochs at q=1.5):
    Run until crystallized (H < 0.95 for 5-streak). If not crystallized by
    epoch 200, seed is excluded from Phase 2/3 (cannot test irreversibility
    without a baseline crystallized state).

  Phase 2 — Overload (150 epochs at q=50.0):
    Extreme query cost forcing energy depletion and protocol breakdown.
    Target: QRC < 0.10 by end of phase (confirmed collapse).

  Phase 3 — Recovery (150 epochs at q=1.5, same as Phase 1):
    Restore original cost. Measure whether the protocol recrystallizes
    and whether the recovery metrics match the pre-overload baseline.

Total: 500 epochs per seed (matching campaign standard).

Outcome measures:
  1. crystallized_phase1: bool — did seed crystallize in Phase 1?
  2. crys_epoch_phase1: crystallization epoch in Phase 1
  3. entropy_end_phase1: type_entropy at epoch 199 (pre-overload baseline)
  4. qrc_end_phase1: QRC at epoch 199 (pre-overload baseline)
  5. entropy_end_phase2: type_entropy at epoch 349 (post-overload)
  6. qrc_end_phase2: QRC at epoch 349 (post-overload)
  7. recrystallized_phase3: bool — H < 0.95 for 5-streak in Phase 3?
  8. recrys_epoch_phase3: first epoch of recrystallization streak in Phase 3
  9. entropy_end_phase3: type_entropy at epoch 499 (final recovery)
  10. qrc_end_phase3: QRC at epoch 499 (final recovery)
  11. recovery_deficit_entropy: entropy_end_phase3 - entropy_end_phase1 (>0 = worse)
  12. irreversibility_detected: bool — NOT recrystallized in Phase 3, OR
      entropy_end_phase3 significantly higher than entropy_end_phase1

Usage
-----
  python run_exp12_irreversibility.py
  python run_exp12_irreversibility.py --workers 4
  python run_exp12_irreversibility.py --dry-run
  python run_exp12_irreversibility.py --analyze-only

Output
------
  data/exp12_irreversibility/seed_{s:02d}/phase_metrics.json
  data/exp12_irreversibility/exp12_summary.json
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

SEEDS           = list(range(15))
EPISODES        = 10
DECLARE_COST    = 1.0
RESPOND_COST    = 0.8

PHASE1_EPOCHS   = 200   # crystallization phase
PHASE2_EPOCHS   = 150   # overload phase
PHASE3_EPOCHS   = 150   # recovery phase
TOTAL_EPOCHS    = PHASE1_EPOCHS + PHASE2_EPOCHS + PHASE3_EPOCHS  # = 500

QUERY_COST_NORM = 1.5   # Phase 1 and Phase 3
QUERY_COST_OVL  = 50.0  # Phase 2 overload

ENTROPY_CRYS_THRESHOLD  = 0.95
ENTROPY_STREAK          = 5
IRREVERSIBILITY_DEFICIT = 0.10  # entropy_end_phase3 > end_phase1 + this → irreversible


# ── Worker ─────────────────────────────────────────────────────────────────────

def _run_one(spec: dict) -> dict:
    """Run one seed through all three phases. Called in subprocess."""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from simulation.engine import SimulationEngine, SimulationConfig

    seed    = spec["seed"]
    out_dir = spec["output_dir"]

    # ── Build a single 500-epoch engine with cost mutation at phase boundaries ──
    phase_boundaries = {
        PHASE1_EPOCHS:               QUERY_COST_OVL,   # start of Phase 2
        PHASE1_EPOCHS + PHASE2_EPOCHS: QUERY_COST_NORM, # start of Phase 3
    }
    phase_log = []

    config = SimulationConfig(
        seed=seed,
        num_epochs=TOTAL_EPOCHS,
        episodes_per_epoch=EPISODES,
        protocol=1,
        declare_cost=DECLARE_COST,
        query_cost=QUERY_COST_NORM,   # Phase 1 starts normal
        respond_cost=RESPOND_COST,
        output_dir=out_dir,
    )
    engine = SimulationEngine(config=config)

    original_run_epoch = engine._run_epoch

    def patched_run_epoch(epoch: int) -> dict:
        if epoch in phase_boundaries:
            engine.protocol.query_cost = phase_boundaries[epoch]
        phase = ("phase1" if epoch < PHASE1_EPOCHS
                 else "phase2" if epoch < PHASE1_EPOCHS + PHASE2_EPOCHS
                 else "phase3")
        phase_log.append({"epoch": epoch, "phase": phase,
                          "query_cost": engine.protocol.query_cost})
        metrics = original_run_epoch(epoch)
        metrics["phase"] = phase
        return metrics

    engine._run_epoch = patched_run_epoch
    engine.run()

    ems = engine.epoch_metrics
    return _analyze(ems, phase_log, seed)


def _analyze(ems: list[dict], phase_log: list[dict], seed: int) -> dict:
    """Extract per-phase metrics from epoch_metrics."""

    def _entropy(m):
        return m.get("inquiry", {}).get("type_entropy")

    def _qrc(m):
        return m.get("inquiry", {}).get("query_response_coupling")

    def _mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 6) if xs else None

    # Split by phase
    p1 = [m for m in ems if m.get("phase") == "phase1"]
    p2 = [m for m in ems if m.get("phase") == "phase2"]
    p3 = [m for m in ems if m.get("phase") == "phase3"]

    # Phase 1 crystallization
    crys_epoch_p1 = None
    streak = 0
    for m in p1:
        h = _entropy(m)
        if h is not None and h < ENTROPY_CRYS_THRESHOLD:
            streak += 1
            if streak >= ENTROPY_STREAK and crys_epoch_p1 is None:
                crys_epoch_p1 = m["epoch"] - ENTROPY_STREAK + 1
        else:
            streak = 0

    # Phase 3 recrystallization
    recrys_epoch_p3 = None
    streak = 0
    for m in p3:
        h = _entropy(m)
        if h is not None and h < ENTROPY_CRYS_THRESHOLD:
            streak += 1
            if streak >= ENTROPY_STREAK and recrys_epoch_p3 is None:
                recrys_epoch_p3 = m["epoch"] - ENTROPY_STREAK + 1
        else:
            streak = 0

    # End-of-phase snapshots (mean over last 10 epochs of each phase)
    def _tail_mean_entropy(phase_ems):
        return _mean([_entropy(m) for m in phase_ems[-10:]])

    def _tail_mean_qrc(phase_ems):
        return _mean([_qrc(m) for m in phase_ems[-10:]])

    e1 = _tail_mean_entropy(p1)
    e2 = _tail_mean_entropy(p2)
    e3 = _tail_mean_entropy(p3)
    q1 = _tail_mean_qrc(p1)
    q2 = _tail_mean_qrc(p2)
    q3 = _tail_mean_qrc(p3)

    recovery_deficit = round(e3 - e1, 4) if (e3 is not None and e1 is not None) else None
    irreversible = (
        recrys_epoch_p3 is None
        or (recovery_deficit is not None and recovery_deficit > IRREVERSIBILITY_DEFICIT)
    )

    return {
        "seed":                      seed,
        # Phase 1
        "crystallized_phase1":       crys_epoch_p1 is not None,
        "crys_epoch_phase1":         crys_epoch_p1,
        "entropy_end_phase1":        e1,
        "qrc_end_phase1":            q1,
        # Phase 2
        "entropy_end_phase2":        e2,
        "qrc_end_phase2":            q2,
        "collapse_detected":         q2 is not None and q2 < 0.10,
        # Phase 3
        "recrystallized_phase3":     recrys_epoch_p3 is not None,
        "recrys_epoch_phase3":       recrys_epoch_p3,
        "entropy_end_phase3":        e3,
        "qrc_end_phase3":            q3,
        # Irreversibility
        "recovery_deficit_entropy":  recovery_deficit,
        "irreversibility_detected":  irreversible,
    }


# ── Campaign runner ────────────────────────────────────────────────────────────

def run_campaign(seeds: list[int], workers: int, dry_run: bool,
                 data_root: Path) -> list[dict]:
    jobs = []
    for seed in seeds:
        out_dir = data_root / f"seed_{seed:02d}"
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
        jobs.append({"seed": seed, "output_dir": str(out_dir)})

    print(f"\nExp 12 -- Irreversibility test")
    print(f"  Phase 1: {PHASE1_EPOCHS} epochs at q={QUERY_COST_NORM} (crystallization)")
    print(f"  Phase 2: {PHASE2_EPOCHS} epochs at q={QUERY_COST_OVL} (overload)")
    print(f"  Phase 3: {PHASE3_EPOCHS} epochs at q={QUERY_COST_NORM} (recovery)")
    print(f"  seeds:   {seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)")
    print(f"  workers: {workers}  |  output: {data_root}")

    if dry_run:
        for j in jobs[:5]:
            print(f"  DRY-RUN: seed={j['seed']}")
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
                p1c   = "CRYS" if r["crystallized_phase1"] else "    "
                p2c   = "COLL" if r.get("collapse_detected") else "    "
                p3r   = "RECRYS" if r["recrystallized_phase3"] else "      "
                irrev = "IRREV" if r["irreversibility_detected"] else "     "
                dfct  = f"{r['recovery_deficit_entropy']:+.3f}" \
                        if r["recovery_deficit_entropy"] is not None else "  N/A"
                print(f"  [{done:2d}/{len(jobs)}]  seed={r['seed']:02d}"
                      f"  {p1c}@{str(r['crys_epoch_phase1'] or '--'):>4}"
                      f"  {p2c}  {p3r}"
                      f"  {irrev}  deficit={dfct}")
            except Exception as e:
                j = futures[fut]
                print(f"  ERROR: seed={j['seed']}: {e}")

    print(f"\nExp 12 done: {done}/{len(jobs)} runs in {time.time()-t0:.0f}s")
    return results


# ── Summary ────────────────────────────────────────────────────────────────────

def write_summary(results: list[dict], data_root: Path) -> None:
    if not results:
        return

    def _mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 4) if xs else None

    n = len(results)
    crys_p1   = [r for r in results if r["crystallized_phase1"]]
    recrys_p3 = [r for r in results if r["recrystallized_phase3"]]
    irrev     = [r for r in results if r["irreversibility_detected"]]

    summary = {
        "experiment":   "12",
        "description":  "Irreversibility test",
        "generated":    datetime.now().isoformat(),
        "phases": {
            "phase1_epochs":   PHASE1_EPOCHS,
            "phase2_epochs":   PHASE2_EPOCHS,
            "phase3_epochs":   PHASE3_EPOCHS,
            "query_cost_norm": QUERY_COST_NORM,
            "query_cost_overload": QUERY_COST_OVL,
        },
        "n_seeds":                     n,
        "n_crystallized_phase1":       len(crys_p1),
        "crystallization_rate_phase1": round(len(crys_p1) / n, 4),
        "n_recrystallized_phase3":     len(recrys_p3),
        "recrystallization_rate_phase3": round(len(recrys_p3) / n, 4),
        "n_irreversible":              len(irrev),
        "irreversibility_rate":        round(len(irrev) / n, 4),
        "mean_recovery_deficit_entropy": _mean([r["recovery_deficit_entropy"]
                                                for r in results]),
        "mean_entropy_end_phase1":     _mean([r["entropy_end_phase1"] for r in results]),
        "mean_entropy_end_phase2":     _mean([r["entropy_end_phase2"] for r in results]),
        "mean_entropy_end_phase3":     _mean([r["entropy_end_phase3"] for r in results]),
        "mean_qrc_end_phase1":         _mean([r["qrc_end_phase1"] for r in results]),
        "mean_qrc_end_phase2":         _mean([r["qrc_end_phase2"] for r in results]),
        "mean_qrc_end_phase3":         _mean([r["qrc_end_phase3"] for r in results]),
        "per_seed": sorted(results, key=lambda r: r["seed"]),
    }

    out = data_root / "exp12_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nExp 12 summary: {out}")

    ag = summary
    print(f"\n  Crystallized Phase 1: {ag['n_crystallized_phase1']}/{n} "
          f"({ag['crystallization_rate_phase1']*100:.0f}%)")
    print(f"  Recrystallized Phase 3: {ag['n_recrystallized_phase3']}/{n} "
          f"({ag['recrystallization_rate_phase3']*100:.0f}%)")
    print(f"  Irreversible: {ag['n_irreversible']}/{n} "
          f"({ag['irreversibility_rate']*100:.0f}%)")
    print(f"  Mean entropy:  P1={ag['mean_entropy_end_phase1']}  "
          f"P2={ag['mean_entropy_end_phase2']}  P3={ag['mean_entropy_end_phase3']}")
    print(f"  Mean QRC:      P1={ag['mean_qrc_end_phase1']}  "
          f"P2={ag['mean_qrc_end_phase2']}  P3={ag['mean_qrc_end_phase3']}")
    print(f"  Mean recovery deficit: {ag['mean_recovery_deficit_entropy']}")

    print(f"\n  {'seed':>4}  {'P1':>4}  {'crys@':>6}  "
          f"{'H_p1':>6}  {'H_p2':>6}  {'H_p3':>6}  "
          f"{'recrys':>6}  {'deficit':>7}  {'irrev':>5}")
    for r in sorted(results, key=lambda x: x["seed"]):
        def _f(v): return f"{v:.3f}" if v is not None else " None"
        p1s  = "CRYS" if r["crystallized_phase1"] else "    "
        p3s  = "YES " if r["recrystallized_phase3"] else " NO "
        ivs  = " YES" if r["irreversibility_detected"] else "    "
        dfct = f"{r['recovery_deficit_entropy']:+.3f}" \
               if r["recovery_deficit_entropy"] is not None else "   N/A"
        print(f"  {r['seed']:>4d}  {p1s}  {str(r['crys_epoch_phase1'] or '--'):>5}  "
              f"{_f(r['entropy_end_phase1'])}  {_f(r['entropy_end_phase2'])}  "
              f"{_f(r['entropy_end_phase3'])}  {p3s}  {dfct}  {ivs}")


# ── Analyze-only ───────────────────────────────────────────────────────────────

def analyze_only(seeds: list[int], data_root: Path) -> None:
    results = []
    for seed in seeds:
        p = data_root / f"seed_{seed:02d}" / "phase_metrics.json"
        if p.exists():
            with open(p) as f:
                results.append(json.load(f))
        else:
            print(f"  WARNING: missing {p}")
    if results:
        write_summary(results, data_root)
    else:
        print("  No data found.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exp 12 -- Irreversibility test (overload then restore)")
    parser.add_argument("--seeds",        type=int, nargs=2, default=[0, 15],
                        metavar=("START", "END"))
    parser.add_argument("--workers",      type=int, default=None)
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--data-dir",     type=str,
                        default=str(Path(__file__).parent.parent / "data" / "exp12_irreversibility"))
    args = parser.parse_args()

    seeds     = list(range(args.seeds[0], args.seeds[1]))
    workers   = args.workers or max(1, (os.cpu_count() or 4) - 1)
    data_root = Path(args.data_dir)

    print(f"Exp 12 -- Irreversibility  --  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]}  Workers: {workers}  Data: {data_root}")

    if args.analyze_only:
        analyze_only(seeds, data_root)
        return

    if not args.dry_run:
        data_root.mkdir(parents=True, exist_ok=True)

    results = run_campaign(seeds, workers, args.dry_run, data_root)
    if results:
        write_summary(results, data_root)
    print("\nDone.")


if __name__ == "__main__":
    main()
