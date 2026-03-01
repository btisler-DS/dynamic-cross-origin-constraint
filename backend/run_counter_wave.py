"""Counter-Wave Discrimination Campaign — Experiments 3, 4, 5.

Tests three competing hypotheses for the counter-wave phenomenon:
full-survival episodes trigger transient DECLARE spikes that temporarily
reverse entropy reduction before the system re-enters the crystallised regime.

  H1 — Reward artifact: terminal survival bonus makes DECLARE cheap to exploit
  H2 — Phase reset: episode boundary triggers learned mode renegotiation
  H3 — Pragmatic content: DECLARE signals "state achieved"; rebound is pressure relief

Conditions
----------
  baseline    (mode=0): normal Protocol 1 — reference counter-wave pattern
  exp3_nobnd  (mode=3): no boundary — continue for 20 steps after success;
                        spike at reward time -> H1; spike at natural end-step -> H2
  exp4_nobon  (mode=4): survival bonus = 0; spike disappears -> H1; persists -> H2/H3
  exp5_phold  (mode=5): elevated tax for 3 episodes after success; rebound
                        suppressed -> H3; unaffected -> H1/H2

Usage
-----
  python run_counter_wave.py [--seeds 0 1 2 3 4] [--epochs 500] [--output-dir ...]
  python run_counter_wave.py --analyze-only --output-dir ../data/counter_wave
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

# ── Constants ──────────────────────────────────────────────────────────────────

SEEDS    = list(range(5))   # fast crystallisers
EPOCHS   = 500
EPISODES = 10
PROTOCOL = 1
QUERY_COST    = 1.5
DECLARE_COST  = 1.0
RESPOND_COST  = 0.8

CONDITIONS = {
    "baseline":   {"counter_wave_mode": 0, "label": "Baseline (normal)"},
    "exp3_nobnd": {"counter_wave_mode": 3, "label": "Exp 3 — no boundary"},
    "exp4_nobon": {"counter_wave_mode": 4, "label": "Exp 4 — no bonus"},
    "exp5_phold": {"counter_wave_mode": 5, "label": "Exp 5 — pressure hold"},
}

# ── Worker ────────────────────────────────────────────────────────────────────

def run_one(spec: dict) -> dict:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from simulation.engine import SimulationEngine, SimulationConfig

    t0 = time.time()
    cfg = SimulationConfig(
        seed=spec["seed"],
        num_epochs=spec["epochs"],
        episodes_per_epoch=spec["episodes"],
        protocol=PROTOCOL,
        declare_cost=DECLARE_COST,
        query_cost=QUERY_COST,
        respond_cost=RESPOND_COST,
        output_dir=spec["output_dir"],
        counter_wave_mode=spec["counter_wave_mode"],
    )
    engine = SimulationEngine(config=cfg)
    engine.run()

    mf_path = os.path.join(spec["output_dir"], "manifest.json")
    manifest = {}
    if os.path.exists(mf_path):
        with open(mf_path) as f:
            manifest = json.load(f)

    cw = manifest.get("counter_wave_data", {})
    return {
        "condition":           spec["condition"],
        "seed":                spec["seed"],
        "status":              "ok",
        "elapsed_s":           round(time.time() - t0, 1),
        "crystallization_epoch": manifest.get("crystallization_epoch"),
        "n_full_survival":     cw.get("n_full_survival_epochs", 0),
        "n_counter_waves":     cw.get("n_counter_wave_events", 0),
        "declare_at_success":  cw.get("declare_rate_at_success"),
        "declare_baseline":    cw.get("declare_rate_baseline"),
    }


# ── Analysis ──────────────────────────────────────────────────────────────────

def _load_manifest(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def run_analysis(base_output: Path, seeds: list[int]) -> dict:
    """Load manifests for all conditions and build discrimination table."""
    import statistics as st

    condition_stats: dict[str, dict] = {}

    for cond_key, cond_info in CONDITIONS.items():
        cw_events:      list[dict]  = []
        declare_spikes: list[float] = []
        declare_base:   list[float] = []
        n_full_surv:    list[int]   = []
        n_cw_events:    list[int]   = []
        success_steps:  list[int]   = []   # Exp 3: steps at which success occurs

        for seed in seeds:
            mf = _load_manifest(base_output / cond_key / f"seed_{seed:02d}" / "manifest.json")
            if not mf:
                continue
            cw = mf.get("counter_wave_data", {})
            if not cw:
                continue

            n_full_surv.append(cw.get("n_full_survival_epochs", 0))
            n_cw_events.append(cw.get("n_counter_wave_events", 0))
            if cw.get("declare_rate_at_success") is not None:
                declare_spikes.append(cw["declare_rate_at_success"])
            if cw.get("declare_rate_baseline") is not None:
                declare_base.append(cw["declare_rate_baseline"])

            # For Exp 3: collect success_step from per-episode summaries in events
            if cond_key == "exp3_nobnd":
                for ev in cw.get("events", []):
                    for ep in ev.get("success_episodes", []):
                        if ep.get("success_step") is not None:
                            success_steps.append(ep["success_step"])

            cw_events.extend(cw.get("events", [])[:5])  # sample for detail

        def smean(lst): return round(st.mean(lst), 4) if lst else None

        condition_stats[cond_key] = {
            "label":              cond_info["label"],
            "n_seeds":            len(seeds),
            "mean_full_survival": smean(n_full_surv),
            "mean_cw_events":     smean(n_cw_events),
            "declare_at_success": smean(declare_spikes),
            "declare_baseline":   smean(declare_base),
            "declare_spike_delta": (
                round(smean(declare_spikes) - smean(declare_base), 4)
                if smean(declare_spikes) is not None and smean(declare_base) is not None
                else None
            ),
            "mean_success_step":  smean(success_steps) if success_steps else None,
            "sample_events":      cw_events[:3],
        }

    # ── Discrimination logic ──────────────────────────────────────────────────
    verdict = _discriminate(condition_stats)

    return {
        "conditions": condition_stats,
        "verdict": verdict,
    }


def _discriminate(stats: dict) -> dict:
    """Apply H1/H2/H3 discrimination logic to condition comparison table."""
    base  = stats.get("baseline",   {})
    exp3  = stats.get("exp3_nobnd", {})
    exp4  = stats.get("exp4_nobon", {})
    exp5  = stats.get("exp5_phold", {})

    base_cw  = base.get("mean_cw_events")
    exp3_cw  = exp3.get("mean_cw_events")
    exp4_cw  = exp4.get("mean_cw_events")
    exp5_cw  = exp5.get("mean_cw_events")

    base_spike  = base.get("declare_spike_delta")
    exp3_spike  = exp3.get("declare_spike_delta")
    exp4_spike  = exp4.get("declare_spike_delta")
    exp5_spike  = exp5.get("declare_spike_delta")

    h1_support = h2_support = h3_support = 0
    evidence   = []

    # H1: spike disappears when bonus removed (Exp 4)
    if exp4_cw is not None and base_cw is not None:
        ratio = exp4_cw / max(base_cw, 0.001)
        if ratio < 0.5:
            h1_support += 2
            evidence.append(f"Exp4 counter-waves {ratio:.2f}x baseline -> strong H1")
        elif ratio > 0.8:
            evidence.append(f"Exp4 counter-waves {ratio:.2f}x baseline -> H1 weak/absent")

    # H1 vs H2: spike at reward time or boundary time (Exp 3)
    if exp3.get("mean_success_step") is not None:
        ss = exp3["mean_success_step"]
        if ss < 50:   # success happens early in episode; spike must be at reward
            h1_support += 1
            evidence.append(f"Exp3 mean_success_step={ss:.0f} (early) -> spike near reward -> H1")
        else:
            h2_support += 1
            evidence.append(f"Exp3 mean_success_step={ss:.0f} (late) -> spike near boundary -> H2")

    # H2: spike persists without bonus (Exp 4)
    if exp4_cw is not None and base_cw is not None:
        ratio = exp4_cw / max(base_cw, 0.001)
        if ratio > 0.8:
            h2_support += 1
            evidence.append(f"Exp4 spikes persist ({ratio:.2f}x) -> H2 supported")

    # H3: rebound suppressed under pressure (Exp 5)
    if exp5_cw is not None and base_cw is not None:
        ratio = exp5_cw / max(base_cw, 0.001)
        if ratio < 0.5:
            h3_support += 2
            evidence.append(f"Exp5 counter-waves {ratio:.2f}x baseline -> strong H3")
        elif ratio > 0.8:
            evidence.append(f"Exp5 rebound unaffected ({ratio:.2f}x) -> H3 weak")

    # Declare-spike comparison
    for key, label in [("exp4_nobon", "Exp4"), ("exp5_phold", "Exp5")]:
        s = stats.get(key, {}).get("declare_spike_delta")
        b = base_spike
        if s is not None and b is not None:
            evidence.append(f"{label} declare_spike_delta={s:.4f} vs baseline={b:.4f}")

    scores = {"H1": h1_support, "H2": h2_support, "H3": h3_support}
    leading = max(scores, key=lambda k: scores[k])
    if all(v == 0 for v in scores.values()):
        leading = "inconclusive"

    return {
        "scores":   scores,
        "leading":  leading,
        "evidence": evidence,
    }


# ── Progress bar ──────────────────────────────────────────────────────────────

def fmt_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / max(total, 1))
    return "[" + "#" * filled + "." * (width - filled) + "]"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Counter-wave discrimination — Experiments 3, 4, 5"
    )
    parser.add_argument("--seeds",      type=int, nargs="+", default=None)
    parser.add_argument("--epochs",     type=int, default=EPOCHS)
    parser.add_argument("--episodes",   type=int, default=EPISODES)
    parser.add_argument("--workers",    type=int, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--conditions", type=str, nargs="+", default=None,
                        help="Subset of conditions to run, e.g. baseline exp4_nobon")
    args = parser.parse_args()

    seeds = args.seeds if args.seeds else SEEDS
    backend_dir = Path(__file__).parent
    base_output = (
        Path(args.output_dir) if args.output_dir
        else backend_dir.parent / "data" / "counter_wave"
    )

    cond_keys = args.conditions if args.conditions else list(CONDITIONS)
    cpu     = os.cpu_count() or 2
    workers = args.workers if args.workers else max(1, cpu - 1)

    print(f"\n{'=' * 60}")
    print(f"  Counter-Wave Discrimination: Experiments 3–5")
    print(f"{'=' * 60}")
    print(f"  Seeds      : {seeds}")
    print(f"  Conditions : {cond_keys}")
    print(f"  Epochs     : {args.epochs}  Episodes: {args.episodes}")
    print(f"  Workers    : {workers}")
    print(f"  Output     : {base_output}")
    print("=" * 60 + "\n")

    if not args.analyze_only:
        specs = [
            {
                "condition":        cond_key,
                "seed":             seed,
                "output_dir":       str(base_output / cond_key / f"seed_{seed:02d}"),
                "epochs":           args.epochs,
                "episodes":         args.episodes,
                "counter_wave_mode": CONDITIONS[cond_key]["counter_wave_mode"],
            }
            for cond_key in cond_keys
            for seed in seeds
        ]
        total = len(specs)
        campaign_start = time.time()
        done_count = 0

        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_one, s): s for s in specs}
            for future in as_completed(futures):
                result = future.result()
                done_count += 1
                icon = "OK" if result["status"] == "ok" else "!!"
                print(
                    f"  {icon} [{result['condition']:12s}] seed={result['seed']:02d}"
                    f"  full_surv={result['n_full_survival']:3d}"
                    f"  cw_events={result['n_counter_waves']:3d}"
                    f"  {result['elapsed_s']:6.1f}s"
                    f"  {fmt_bar(done_count, total)}"
                )

        elapsed = time.time() - campaign_start
        print(f"\n  Runs complete: {done_count}/{total}  ({elapsed / 60:.1f} min)\n")

    # ── Analysis ──────────────────────────────────────────────────────────────
    print("  Running counter-wave analysis...\n")
    analysis = run_analysis(base_output, seeds)

    cond_stats = analysis["conditions"]
    verdict    = analysis["verdict"]

    # Print discrimination table
    print(f"  {'Condition':<16} {'CW events':>10} {'D@success':>10} {'D@baseline':>10} {'Spike delta':>12}")
    print("  " + "-" * 62)
    for key, cs in cond_stats.items():
        print(
            f"  {key:<16}"
            f"  {str(cs.get('mean_cw_events')):>9}"
            f"  {str(cs.get('declare_at_success')):>9}"
            f"  {str(cs.get('declare_baseline')):>9}"
            f"  {str(cs.get('declare_spike_delta')):>11}"
        )

    print()
    print(f"  H1/H2/H3 scores: {verdict['scores']}")
    print(f"  Leading hypothesis: {verdict['leading']}")
    print()
    for line in verdict["evidence"]:
        print(f"    - {line}")

    # Write summary
    summary = {
        "experiment":     "counter_wave_discrimination",
        "campaign_date":  datetime.now().isoformat(),
        "seeds":          seeds,
        "conditions":     cond_keys,
        "epochs":         args.epochs,
        **analysis,
    }
    base_output.mkdir(parents=True, exist_ok=True)
    summary_path = base_output / "counter_wave_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Summary: {summary_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
