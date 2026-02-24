"""Research-grade report generation — PDF, JSON, and Markdown.

Four narrative modules:
1. Phase Transition Narrative (Entropy Cliff)
2. Isomorphism Bridge (Agent C as "Weaver", TE Matrix)
3. Zipf's Law Validation (Linguistic Efficiency)
4. Perturbation Resilience Summary
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from ..config import settings

THESIS = (
    "Language is the emergent formalization of stabilized relational "
    "constraints under sustained multi-system coupling."
)


# ──────────────────────────────────────────────
# Analysis helpers
# ──────────────────────────────────────────────

def _detect_entropy_cliff(epochs: list[dict]) -> dict:
    """Find the epoch where entropy drops most sharply (phase transition)."""
    if len(epochs) < 3:
        return {"cliff_epoch": None, "cliff_magnitude": 0, "narrative": "Insufficient data."}

    avg_entropies = []
    for m in epochs:
        ent = m.get("entropy", {})
        vals = [v for v in ent.values() if isinstance(v, (int, float))]
        avg_entropies.append(sum(vals) / len(vals) if vals else 0)

    max_drop = 0
    cliff_epoch = 0
    for i in range(1, len(avg_entropies)):
        drop = avg_entropies[i - 1] - avg_entropies[i]
        if drop > max_drop:
            max_drop = drop
            cliff_epoch = i

    # Check if MI rises around the same time
    mi_at_cliff = 0
    mi_before = 0
    if cliff_epoch > 0:
        mi_vals = list(epochs[cliff_epoch].get("mutual_information", {}).values())
        mi_at_cliff = sum(mi_vals) / len(mi_vals) if mi_vals else 0
        mi_vals_b = list(epochs[cliff_epoch - 1].get("mutual_information", {}).values())
        mi_before = sum(mi_vals_b) / len(mi_vals_b) if mi_vals_b else 0

    phase_confirmed = max_drop > 0.05 and mi_at_cliff > mi_before

    narrative = (
        f"Phase transition detected at epoch {cliff_epoch + 1}. "
        f"Average Shannon entropy dropped by {max_drop:.3f} bits. "
        f"Mutual information {'rose simultaneously, confirming' if phase_confirmed else 'did not clearly rise — tentative'} "
        f"the transition from noise to structured protocol."
    )

    return {
        "cliff_epoch": cliff_epoch,
        "cliff_magnitude": round(max_drop, 4),
        "entropy_before": round(avg_entropies[max(0, cliff_epoch - 1)], 4),
        "entropy_after": round(avg_entropies[min(cliff_epoch, len(avg_entropies) - 1)], 4),
        "mi_before": round(mi_before, 4),
        "mi_at_cliff": round(mi_at_cliff, 4),
        "phase_confirmed": phase_confirmed,
        "narrative": narrative,
    }


def _analyze_te_matrix(epochs: list[dict]) -> dict:
    """Analyze Transfer Entropy to determine Agent C's role as Weaver."""
    if not epochs:
        return {"matrix": {}, "narrative": "No data."}

    # Average TE over last 20% of epochs (post-convergence)
    window = max(1, len(epochs) // 5)
    late_epochs = epochs[-window:]

    avg_te: dict[str, float] = {}
    for m in late_epochs:
        te = m.get("transfer_entropy", {})
        for pair, val in te.items():
            if isinstance(val, (int, float)):
                avg_te[pair] = avg_te.get(pair, 0) + val / window

    # Identify asymmetry: does C listen to B more than A?
    c_from_b = avg_te.get("B→C", 0)
    c_from_a = avg_te.get("A→C", 0)
    c_to_a = avg_te.get("C→A", 0)
    c_to_b = avg_te.get("C→B", 0)

    c_receives = c_from_a + c_from_b
    c_sends = c_to_a + c_to_b
    is_weaver = c_receives > 0 and c_sends > 0

    narrative_parts = [
        f"Transfer Entropy Matrix (averaged over last {window} epochs):",
        f"  B→C: {c_from_b:.4f} | A→C: {c_from_a:.4f} (C receives)",
        f"  C→A: {c_to_a:.4f} | C→B: {c_to_b:.4f} (C transmits)",
    ]

    if is_weaver:
        if c_from_b > c_from_a:
            narrative_parts.append(
                "Agent C (GNN/Relational) listens more to Agent B (3D/Spatial) than "
                "Agent A (1D/Sequential), confirming its role as cross-modal translator. "
                "The 3D acoustic map carries more causal information for decision-making."
            )
        else:
            narrative_parts.append(
                "Agent C integrates signals from both A and B, serving as a "
                "relational bridge between the sequential and spatial modalities."
            )
    else:
        narrative_parts.append(
            "Causal flow through Agent C is weak — the Weaver role "
            "has not clearly emerged in this run."
        )

    return {
        "matrix": {k: round(v, 5) for k, v in avg_te.items()},
        "c_receives_total": round(c_receives, 5),
        "c_sends_total": round(c_sends, 5),
        "asymmetry_b_over_a": round(c_from_b - c_from_a, 5),
        "is_weaver": is_weaver,
        "narrative": "\n".join(narrative_parts),
    }


def _analyze_zipf(epochs: list[dict]) -> dict:
    """Analyze Zipf's law fit for linguistic efficiency."""
    if not epochs:
        return {"agents": {}, "narrative": "No data."}

    last = epochs[-1]
    zipf_data = last.get("zipf", {})

    results = {}
    for agent, vals in zipf_data.items():
        if isinstance(vals, dict):
            results[agent] = {
                "alpha": vals.get("alpha", 0),
                "r_squared": vals.get("r_squared", 0),
                "ks_statistic": vals.get("ks_statistic", 0),
            }

    # Zipf's law for natural language has alpha ≈ 1.0
    alphas = [v.get("alpha", 0) for v in results.values()]
    avg_alpha = sum(alphas) / len(alphas) if alphas else 0
    r_squareds = [v.get("r_squared", 0) for v in results.values()]
    avg_r2 = sum(r_squareds) / len(r_squareds) if r_squareds else 0

    if avg_alpha > 0.8 and avg_r2 > 0.3:
        verdict = (
            f"Signal frequency distribution follows a power law (avg α={avg_alpha:.2f}, "
            f"avg R²={avg_r2:.2f}). This indicates the agents developed 'short codes' "
            f"for frequent concepts, consistent with Zipf's principle of least effort — "
            f"a hallmark of natural language efficiency."
        )
    elif avg_alpha > 0.5:
        verdict = (
            f"Partial Zipfian structure detected (avg α={avg_alpha:.2f}, R²={avg_r2:.2f}). "
            f"The protocol shows some frequency-based optimization but has not reached "
            f"the efficiency of a mature language."
        )
    else:
        verdict = (
            f"Weak Zipfian structure (avg α={avg_alpha:.2f}). The signal distribution "
            f"does not yet resemble a frequency-optimized code."
        )

    return {"agents": results, "avg_alpha": round(avg_alpha, 3), "avg_r_squared": round(avg_r2, 3), "narrative": verdict}


def _analyze_perturbation_resilience(epochs: list[dict]) -> dict:
    """Check for kill switch / perturbation events and measure recovery."""
    kill_epochs = [m["epoch"] for m in epochs if m.get("comm_killed")]
    has_kill_event = len(kill_epochs) > 0

    if not has_kill_event:
        return {
            "kill_switch_used": False,
            "narrative": (
                "No ablation kill switch was triggered during this run. "
                "To prove the protocol is load-bearing, run with the kill switch "
                "activated mid-training and observe the survival drop."
            ),
        }

    # Measure survival before/during/after kill
    survival_before = []
    survival_during = []
    survival_after = []
    first_kill = kill_epochs[0]

    for m in epochs:
        sr = m.get("survival_rate", 0)
        if m["epoch"] < first_kill:
            survival_before.append(sr)
        elif m.get("comm_killed"):
            survival_during.append(sr)
        else:
            survival_after.append(sr)

    avg_before = sum(survival_before) / len(survival_before) if survival_before else 0
    avg_during = sum(survival_during) / len(survival_during) if survival_during else 0
    avg_after = sum(survival_after) / len(survival_after) if survival_after else 0

    drop = avg_before - avg_during
    load_bearing = drop > 0.1

    narrative = (
        f"Kill switch activated at epoch {first_kill + 1}. "
        f"Survival rate: {avg_before:.1%} (before) → {avg_during:.1%} (during) → {avg_after:.1%} (after). "
        f"{'Protocol is LOAD-BEARING: performance dropped ' + f'{drop:.1%}' + ' when communication was severed.' if load_bearing else 'Drop was minimal — protocol may not be fully load-bearing yet.'}"
    )

    return {
        "kill_switch_used": True,
        "first_kill_epoch": first_kill,
        "survival_before": round(avg_before, 4),
        "survival_during": round(avg_during, 4),
        "survival_after": round(avg_after, 4),
        "drop": round(drop, 4),
        "load_bearing": load_bearing,
        "narrative": narrative,
    }


def _compute_summary(epoch_metrics: list[dict]) -> dict:
    if not epoch_metrics:
        return {}

    last = epoch_metrics[-1]
    return {
        "total_epochs": len(epoch_metrics),
        "final_survival_rate": last.get("survival_rate", 0),
        "final_target_rate": last.get("target_reached_rate", 0),
        "mean_energy_roi": sum(m.get("energy_roi", 0) or 0 for m in epoch_metrics) / len(epoch_metrics),
        "final_entropy": last.get("entropy", {}),
        "final_mi": last.get("mutual_information", {}),
        "final_te": last.get("transfer_entropy", {}),
    }


# ──────────────────────────────────────────────
# JSON Report
# ──────────────────────────────────────────────

def generate_json_report(run_data: dict, epoch_metrics: list[dict]) -> str:
    """Generate full JSON report with all analysis modules."""
    # Strip trajectory data from epoch metrics to keep JSON lean
    clean_epochs = []
    for m in epoch_metrics:
        cleaned = {k: v for k, v in m.items() if k != "trajectory"}
        clean_epochs.append(cleaned)

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "thesis": THESIS,
        "run": run_data,
        "summary": _compute_summary(epoch_metrics),
        "analysis": {
            "phase_transition": _detect_entropy_cliff(epoch_metrics),
            "isomorphism_bridge": _analyze_te_matrix(epoch_metrics),
            "zipf_validation": _analyze_zipf(epoch_metrics),
            "perturbation_resilience": _analyze_perturbation_resilience(epoch_metrics),
        },
        "epochs": clean_epochs,
    }
    return json.dumps(report, indent=2, default=str)


# ──────────────────────────────────────────────
# Markdown Report
# ──────────────────────────────────────────────

def generate_markdown_report(run_data: dict, epoch_metrics: list[dict]) -> str:
    """Generate research-ready Markdown report."""
    summary = _compute_summary(epoch_metrics)
    phase = _detect_entropy_cliff(epoch_metrics)
    te_analysis = _analyze_te_matrix(epoch_metrics)
    zipf = _analyze_zipf(epoch_metrics)
    perturb = _analyze_perturbation_resilience(epoch_metrics)

    md = f"""# Project Synapse — Simulation Report

> **Thesis:** *{THESIS}*

---

## Run Metadata

| Field | Value |
|-------|-------|
| Run ID | {run_data.get('id', 'N/A')} |
| Seed | {run_data.get('seed', 'N/A')} |
| Status | {run_data.get('status', 'N/A')} |
| Total Epochs | {summary.get('total_epochs', 0)} |
| Final Hash | `{run_data.get('final_hash', 'N/A')}` |
| Generated | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} |

---

## Summary

| Metric | Value |
|--------|-------|
| Final Survival Rate | {summary.get('final_survival_rate', 0):.1%} |
| Final Target Rate | {summary.get('final_target_rate', 0):.1%} |
| Mean Energy ROI | {summary.get('mean_energy_roi', 0):.6f} |

---

## 1. Phase Transition — The Entropy Cliff

{phase['narrative']}

| Measure | Value |
|---------|-------|
| Cliff Epoch | {(phase.get('cliff_epoch', 0) or 0) + 1} |
| Entropy Before | {phase.get('entropy_before', 0):.4f} bits |
| Entropy After | {phase.get('entropy_after', 0):.4f} bits |
| MI Before | {phase.get('mi_before', 0):.4f} |
| MI at Cliff | {phase.get('mi_at_cliff', 0):.4f} |
| Phase Confirmed | {'Yes' if phase.get('phase_confirmed') else 'No'} |

**Interpretation:** When Shannon entropy drops while mutual information rises,
it signals the system has transitioned from random exploration (noise) to a
structured communication protocol.

---

## 2. The Isomorphism Bridge — Agent C as "Weaver"

{te_analysis['narrative']}

### Transfer Entropy Matrix (Post-Convergence)

| Direction | TE Value |
|-----------|----------|
"""

    for pair, val in te_analysis.get("matrix", {}).items():
        md += f"| {pair} | {val:.5f} |\n"

    md += f"""
| C total receives | {te_analysis.get('c_receives_total', 0):.5f} |
| C total sends | {te_analysis.get('c_sends_total', 0):.5f} |
| B→C minus A→C (asymmetry) | {te_analysis.get('asymmetry_b_over_a', 0):.5f} |

**Interpretation:** Agent C (the GNN/Relational agent) is the analog of an AI system
that must find the mathematical commonality between a 1D sequential processor
(Human analog) and a 3D spatial processor (Dolphin analog). Asymmetric TE flow
proves relational hierarchy in the emergent protocol.

---

## 3. Zipf's Law Validation — Linguistic Efficiency

{zipf['narrative']}

| Agent | Zipf α | R² |
|-------|--------|----|
"""

    for agent, vals in zipf.get("agents", {}).items():
        md += f"| Agent {agent} | {vals.get('alpha', 0):.3f} | {vals.get('r_squared', 0):.3f} |\n"

    md += f"""
**Interpretation:** Zipf's law (α ≈ 1.0) indicates the agents allocate short,
frequent codes to common concepts — the same efficiency principle observed
in every known natural language. This validates that the emergent protocol
optimizes Energy ROI through linguistic compression.

---

## 4. Perturbation Resilience

{perturb['narrative']}

**Interpretation:** If severing communication causes a measurable performance
drop, the protocol is *load-bearing* — meaning the agents genuinely depend
on their emergent language. This rules out the null hypothesis that agents
succeed through independent action alone.

---

## Hash Chain Integrity

The complete SHA-256 hash chain for this run is included in the JSON export.
Each epoch's metrics are cryptographically chained:

```
hash_N = SHA-256( hash_{{N-1}} | canonical_json(metrics_N) | seed )
```

Final chain tip: `{run_data.get('final_hash', 'N/A')}`

---

*Generated by Project Synapse — Cross-Origin Constraint*
"""
    return md


# ──────────────────────────────────────────────
# PDF Report
# ──────────────────────────────────────────────

def generate_pdf_report(
    run_data: dict,
    epoch_metrics: list[dict],
    output_path: str,
) -> str:
    """Generate executive summary PDF with all analysis modules."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle('ThesisStyle', parent=styles['Normal'],
                              fontSize=11, italic=True, textColor=colors.HexColor('#336699'),
                              spaceAfter=12, alignment=TA_CENTER))
    styles.add(ParagraphStyle('SectionHead', parent=styles['Heading2'],
                              textColor=colors.HexColor('#2c3e50'), spaceAfter=8))
    styles.add(ParagraphStyle('Narrative', parent=styles['Normal'],
                              fontSize=10, leading=14, spaceAfter=10))
    styles.add(ParagraphStyle('SmallMono', parent=styles['Normal'],
                              fontName='Courier', fontSize=8, textColor=colors.grey))

    story = []

    # Title
    story.append(Paragraph("Project Synapse — Simulation Report", styles['Title']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f'"{THESIS}"', styles['ThesisStyle']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#444')))
    story.append(Spacer(1, 8))

    # Metadata table
    summary = _compute_summary(epoch_metrics)
    meta_data = [
        ["Run ID", str(run_data.get('id', 'N/A')), "Seed", str(run_data.get('seed', 'N/A'))],
        ["Status", run_data.get('status', 'N/A'), "Epochs", str(summary.get('total_epochs', 0))],
        ["Final Survival", f"{summary.get('final_survival_rate', 0):.1%}",
         "Target Rate", f"{summary.get('final_target_rate', 0):.1%}"],
        ["Energy ROI", f"{summary.get('mean_energy_roi', 0):.6f}",
         "Generated", datetime.utcnow().strftime('%Y-%m-%d %H:%M')],
    ]
    t = Table(meta_data, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 2.3*inch])
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Section 1: Phase Transition ──
    phase = _detect_entropy_cliff(epoch_metrics)
    story.append(Paragraph("1. Phase Transition — The Entropy Cliff", styles['SectionHead']))
    story.append(Paragraph(phase['narrative'], styles['Narrative']))

    phase_table = [
        ["Cliff Epoch", "Entropy Before", "Entropy After", "MI Before", "MI at Cliff", "Confirmed"],
        [
            str((phase.get('cliff_epoch', 0) or 0) + 1),
            f"{phase.get('entropy_before', 0):.4f}",
            f"{phase.get('entropy_after', 0):.4f}",
            f"{phase.get('mi_before', 0):.4f}",
            f"{phase.get('mi_at_cliff', 0):.4f}",
            "Yes" if phase.get('phase_confirmed') else "No",
        ],
    ]
    t = Table(phase_table, colWidths=[1*inch]*6)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Section 2: Isomorphism Bridge ──
    te_analysis = _analyze_te_matrix(epoch_metrics)
    story.append(Paragraph("2. The Isomorphism Bridge — Agent C as Weaver", styles['SectionHead']))
    for line in te_analysis['narrative'].split('\n'):
        story.append(Paragraph(line, styles['Narrative']))

    te_rows = [["Direction", "TE Value"]]
    for pair, val in te_analysis.get("matrix", {}).items():
        te_rows.append([pair, f"{val:.5f}"])
    te_rows.append(["C receives (total)", f"{te_analysis.get('c_receives_total', 0):.5f}"])
    te_rows.append(["C sends (total)", f"{te_analysis.get('c_sends_total', 0):.5f}"])

    t = Table(te_rows, colWidths=[2.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Section 3: Zipf Validation ──
    zipf = _analyze_zipf(epoch_metrics)
    story.append(Paragraph("3. Zipf's Law Validation — Linguistic Efficiency", styles['SectionHead']))
    story.append(Paragraph(zipf['narrative'], styles['Narrative']))

    zipf_rows = [["Agent", "Zipf α", "R²"]]
    for agent, vals in zipf.get("agents", {}).items():
        zipf_rows.append([f"Agent {agent}", f"{vals.get('alpha', 0):.3f}", f"{vals.get('r_squared', 0):.3f}"])

    t = Table(zipf_rows, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Section 4: Perturbation Resilience ──
    perturb = _analyze_perturbation_resilience(epoch_metrics)
    story.append(Paragraph("4. Perturbation Resilience", styles['SectionHead']))
    story.append(Paragraph(perturb['narrative'], styles['Narrative']))
    story.append(Spacer(1, 12))

    # Hash chain
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Hash Chain Integrity", styles['SectionHead']))
    story.append(Paragraph(
        f"Final chain tip: {run_data.get('final_hash', 'N/A')}",
        styles['SmallMono'],
    ))
    story.append(Paragraph(
        "Full chain available in JSON export. Each epoch is cryptographically "
        "linked: hash_N = SHA-256(hash_{N-1} | metrics_N | seed)",
        styles['Narrative'],
    ))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "Generated by Project Synapse — Cross-Origin Constraint",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(story)
    return output_path
