"""Bridge formation campaign runner — Experiment B.

Preregistered in: docs/preregistration-ant-modules.md (locked 2026-03-01)

Experiment B — Gap-size hysteresis:
  30 seeds x 1 ramp protocol = 30 runs
  Ramp: warmup(500) + up(gap_min=1..gap_max=30, 500 steps each) +
        down(gap_max=30..gap_min=1, 500 steps each)
  Total steps per run: 500 + 30*500 + 30*500 = 30500 steps

Usage
-----
  python run_bridge_campaign.py                # all 30 seeds
  python run_bridge_campaign.py --workers 4
  python run_bridge_campaign.py --seeds 0 10  # seeds 0..9
  python run_bridge_campaign.py --dry-run
  python run_bridge_campaign.py --analyze-only # reread existing manifests

Output
------
  data/ant_experiments/exp_b/seed_{s:02d}/manifest.json
  data/ant_experiments/exp_b_summary.json
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

from simulation.ants.bridge import BridgeConfig, BridgeSimulation

# ── Preregistered parameters ──────────────────────────────────────────────────

BRIDGE_CFG_DEFAULTS = dict(
    corridor_length  = 50,
    corridor_width   = 3,
    gap_min          = 1,
    gap_max          = 30,
    hold_steps       = 500,
    min_jump_size    = 3,    # gaps <= this are directly traversable (no bridge needed)
    join_threshold   = 1,
    traffic_window   = 5,
    reid_coefficient = 0.51,
    leave_patience   = 5,
    n_ants           = 100,
)


# ── Per-run worker ────────────────────────────────────────────────────────────

def _run_one(args: tuple) -> dict:
    """Run one Exp B seed. Called in subprocess via ProcessPoolExecutor."""
    seed, output_dir_str = args
    cfg = BridgeConfig(**BRIDGE_CFG_DEFAULTS, seed=seed, output_dir=output_dir_str)
    sim = BridgeSimulation(cfg, gap_size=cfg.gap_min)
    sim.run_ramp()
    sim.write_manifest()

    hys_mag = None
    if sim.formation_gap is not None and sim.dissolution_gap is not None:
        hys_mag = sim.formation_gap - sim.dissolution_gap

    return {
        "seed":                  seed,
        "formation_gap":         sim.formation_gap,
        "dissolution_gap":       sim.dissolution_gap,
        "hysteresis_detected":   sim.hysteresis_detected,
        "hysteresis_magnitude":  hys_mag,
        "mean_bridge_size":      sim.mean_bridge_size(),
        "throughput":            sim.throughput(),
        "max_bridge_size":       max(sim.bridge_size_history)
                                 if sim.bridge_size_history else 0,
        "bridge_size_up":        sim.bridge_size_up,
        "bridge_size_down":      sim.bridge_size_down,
    }


# ── Campaign runner ───────────────────────────────────────────────────────────

def run_exp_b(seeds: list[int], workers: int, dry_run: bool,
              data_root: Path) -> list[dict]:
    """Run Experiment B: gap-size hysteresis ramp."""
    out_root = data_root / "exp_b"
    jobs = []
    for seed in seeds:
        out_dir = out_root / f"seed_{seed:02d}"
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
        jobs.append((seed, str(out_dir)))

    n_steps_per_run = (BRIDGE_CFG_DEFAULTS["hold_steps"] +
                       2 * (BRIDGE_CFG_DEFAULTS["gap_max"] -
                            BRIDGE_CFG_DEFAULTS["gap_min"] + 1) *
                       BRIDGE_CFG_DEFAULTS["hold_steps"])
    print(f"\nExp B -- gap-size hysteresis ramp")
    print(f"  seeds:       {seeds[0]}..{seeds[-1]} ({len(seeds)} seeds)")
    print(f"  gap range:   {BRIDGE_CFG_DEFAULTS['gap_min']}..{BRIDGE_CFG_DEFAULTS['gap_max']}")
    print(f"  hold_steps:  {BRIDGE_CFG_DEFAULTS['hold_steps']}")
    print(f"  steps/run:   {n_steps_per_run}")
    print(f"  workers:     {workers}")
    print(f"  output:      {out_root}")

    if dry_run:
        for seed, out_dir in jobs[:5]:
            print(f"  DRY-RUN: seed={seed}  -> {out_dir}")
        if len(jobs) > 5:
            print(f"  ... ({len(jobs) - 5} more)")
        return []

    results = []
    t0 = time.time()
    done = 0

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one, job): job for job in jobs}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
                done += 1
                hys_flag = "HYS" if r["hysteresis_detected"] else "   "
                fg = f"{r['formation_gap']:3d}"   if r["formation_gap"]   is not None else " -- "
                dg = f"{r['dissolution_gap']:3d}" if r["dissolution_gap"] is not None else " -- "
                hm = f"{r['hysteresis_magnitude']:3d}" if r["hysteresis_magnitude"] is not None else " -- "
                print(f"  [{done:2d}/{len(jobs)}] {hys_flag}  seed={r['seed']:02d}"
                      f"  form_gap={fg}  diss_gap={dg}  hys_mag={hm}"
                      f"  tp={r['throughput']:.4f}")
            except Exception as e:
                job = futures[fut]
                print(f"  ERROR: seed={job[0]}: {e}")

    elapsed = time.time() - t0
    print(f"\nExp B done: {done}/{len(jobs)} runs in {elapsed:.0f}s")
    return results


# ── Summary writer ────────────────────────────────────────────────────────────

def write_summary_b(results: list[dict], data_root: Path) -> None:
    """Write Exp B summary with per-seed and aggregate hysteresis stats."""
    n = len(results)
    if n == 0:
        return

    hysteretic = [r for r in results if r["hysteresis_detected"]]
    form_gaps  = [r["formation_gap"]   for r in results if r["formation_gap"]   is not None]
    diss_gaps  = [r["dissolution_gap"] for r in results if r["dissolution_gap"] is not None]
    hys_mags   = [r["hysteresis_magnitude"] for r in results
                  if r["hysteresis_magnitude"] is not None]
    hys_mags_pos = [m for m in hys_mags if m > 0]

    def _mean(xs): return round(sum(xs) / len(xs), 2) if xs else None
    def _sd(xs):
        if len(xs) < 2: return None
        mu = sum(xs) / len(xs)
        return round((sum((x - mu)**2 for x in xs) / len(xs)) ** 0.5, 2)

    # Preregistered tests
    n_hysteretic = len(hysteretic)
    # B-H1: >= 20/30 seeds show hysteresis
    bh1_pass = n_hysteretic >= int(2 * n / 3)   # >= 2/3 of seeds
    bh1_note = f"{n_hysteretic}/{n} seeds  (>=20/30 required)"

    # B-H2: bridge_size_down/bridge_size_up ratio > 1.3 at gaps [form_gap, 2*form_gap]
    # Compute mean ratio across seeds for the relevant gap range
    bh2_ratios = []
    for r in results:
        up = r.get("bridge_size_up", {})
        dn = r.get("bridge_size_down", {})
        fg = r.get("formation_gap")
        if not fg or not up or not dn:
            continue
        target_range = range(fg, min(fg * 2 + 1, BRIDGE_CFG_DEFAULTS["gap_max"] + 1))
        for g in target_range:
            u = up.get(g, up.get(str(g), 0.0))
            d = dn.get(g, dn.get(str(g), 0.0))
            if u > 0:
                bh2_ratios.append(d / u)
    mean_bh2_ratio = _mean(bh2_ratios)
    bh2_pass = mean_bh2_ratio is not None and mean_bh2_ratio >= 1.3
    bh2_note = f"mean_ratio={mean_bh2_ratio} (>=1.3 required)"

    # B-H3: mean hysteresis_magnitude >= 1 in hysteretic seeds
    mean_mag_hys = _mean(hys_mags_pos)
    bh3_pass = mean_mag_hys is not None and mean_mag_hys >= 1

    summary = {
        "experiment":        "B",
        "description":       "Gap-size hysteresis ramp",
        "generated":         datetime.now().isoformat(),
        "preregistration":   "docs/preregistration-ant-modules.md",
        "bridge_config":     BRIDGE_CFG_DEFAULTS,
        "n_seeds":           n,
        "aggregate": {
            "n_hysteretic":          n_hysteretic,
            "hysteresis_rate":       round(n_hysteretic / n, 4),
            "B_H1_pass":             bh1_pass,
            "B_H1_note":             bh1_note,
            "mean_formation_gap":    _mean(form_gaps),
            "sd_formation_gap":      _sd(form_gaps),
            "mean_dissolution_gap":  _mean(diss_gaps),
            "sd_dissolution_gap":    _sd(diss_gaps),
            "mean_hysteresis_magnitude_all":          _mean(hys_mags),
            "mean_hysteresis_magnitude_hysteretic":   mean_mag_hys,
            "sd_hysteresis_magnitude_hysteretic":     _sd(hys_mags_pos),
            "B_H2_pass":             bh2_pass,
            "B_H2_note":             bh2_note,
            "B_H3_pass":             bh3_pass,
            "B_H3_note":             f"mean_mag={mean_mag_hys} (>=1 required)",
        },
        "per_seed": sorted(results, key=lambda r: r["seed"]),
    }

    out = data_root / "exp_b_summary.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nExp B summary: {out}")

    # Print aggregate
    ag = summary["aggregate"]
    print(f"\n  Hysteresis detected: {ag['n_hysteretic']}/{n} seeds "
          f"({ag['hysteresis_rate']*100:.1f}%)")
    print(f"  B-H1: {'PASS' if bh1_pass else 'FAIL'}  {ag['B_H1_note']}")
    print(f"  B-H2: {'PASS' if bh2_pass else 'FAIL'}  {ag['B_H2_note']}")
    print(f"  B-H3: {'PASS' if bh3_pass else 'FAIL'}  {ag['B_H3_note']}")
    print(f"  Mean formation_gap:   {ag['mean_formation_gap']}  "
          f"(sd={ag['sd_formation_gap']})")
    print(f"  Mean dissolution_gap: {ag['mean_dissolution_gap']}  "
          f"(sd={ag['sd_dissolution_gap']})")
    print(f"  Mean hys_magnitude (all):       {ag['mean_hysteresis_magnitude_all']}")
    print(f"  Mean hys_magnitude (hysteretic): {ag['mean_hysteresis_magnitude_hysteretic']}")

    # Seed table
    print(f"\n  {'seed':>4}  {'form_gap':>8}  {'diss_gap':>8}  "
          f"{'hys_mag':>7}  {'hys':>4}  {'throughput':>10}")
    for r in sorted(results, key=lambda x: x["seed"]):
        fg  = f"{r['formation_gap']:>8d}"   if r["formation_gap"]   is not None else "    None"
        dg  = f"{r['dissolution_gap']:>8d}" if r["dissolution_gap"] is not None else "    None"
        hm  = f"{r['hysteresis_magnitude']:>7d}" if r["hysteresis_magnitude"] is not None else "   None"
        hys = " YES" if r["hysteresis_detected"] else "    "
        print(f"  {r['seed']:>4d}  {fg}  {dg}  {hm}  {hys}  {r['throughput']:>10.4f}")


# ── Analyze-only mode ─────────────────────────────────────────────────────────

def analyze_only(seeds: list[int], data_root: Path) -> None:
    """Read existing manifests and regenerate summary without running."""
    results = []
    out_root = data_root / "exp_b"
    for seed in seeds:
        p = out_root / f"seed_{seed:02d}" / "manifest.json"
        if not p.exists():
            print(f"  WARNING: missing {p}")
            continue
        with open(p) as f:
            m = json.load(f)
        results.append({
            "seed":                 seed,
            "formation_gap":        m.get("formation_gap"),
            "dissolution_gap":      m.get("dissolution_gap"),
            "hysteresis_detected":  m.get("hysteresis_detected"),
            "hysteresis_magnitude": m.get("hysteresis_magnitude"),
            "mean_bridge_size":     m.get("mean_bridge_size"),
            "throughput":           m.get("throughput"),
            "max_bridge_size":      m.get("max_bridge_size"),
        })
    if results:
        write_summary_b(results, data_root)
    else:
        print("  No manifests found.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bridge formation campaign runner (Experiment B)"
    )
    parser.add_argument("--workers",      type=int, default=None)
    parser.add_argument("--seeds",        type=int, nargs=2, default=[0, 30],
                        metavar=("START", "END"),
                        help="Seed range [start, end) (default: 0 30)")
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--analyze-only", action="store_true",
                        help="Read existing manifests and regenerate summary")
    parser.add_argument("--data-dir",     type=str,
                        default=str(Path(__file__).parent.parent / "data" / "ant_experiments"))
    args = parser.parse_args()

    seeds     = list(range(args.seeds[0], args.seeds[1]))
    workers   = args.workers or max(1, (os.cpu_count() or 4) - 1)
    data_root = Path(args.data_dir)

    print(f"Bridge campaign  --  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]}  Workers: {workers}  Data: {data_root}")

    if args.analyze_only:
        analyze_only(seeds, data_root)
        return

    if not args.dry_run:
        data_root.mkdir(parents=True, exist_ok=True)

    results = run_exp_b(seeds, workers, args.dry_run, data_root)
    if results:
        write_summary_b(results, data_root)

    print("\nDone.")


if __name__ == "__main__":
    main()
