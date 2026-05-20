# Dynamic Cross-Origin Constraint

**Experimental harness for the Δ-Variable Theory of Interrogative Emergence.**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18738379.svg)](https://doi.org/10.5281/zenodo.18738379)
[![Status: Ongoing](https://img.shields.io/badge/status-ongoing-blue)]()
[![Preregistered](https://img.shields.io/badge/preregistered-zenodo-green)]()
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

---

## What This Is

A multi-agent reinforcement learning system in which three heterogeneous agents (RNN · CNN · GNN) coordinate under energy constraints. Under Protocol 1, interrogative signal types — query/response structures — emerge spontaneously. Agents develop question-asking behavior because resolving uncertainty is cheaper than acting blindly.

This is the confirmatory experimental platform for the preregistered study:

> *Testing Substrate-Independent Emergence of Interrogative Structures Under Resource Constraints in Multi-Agent Coordination Systems*
> **DOI:** [10.5281/zenodo.18738379](https://doi.org/10.5281/zenodo.18738379)

The theory being tested: **questions are not a linguistic accident — they are a structural necessity**. Any coupled system facing coordination challenges under metabolic pressure will spontaneously develop interrogative protocols as the optimal solution to managing unresolved dependencies (Δ-variables). The mathematical signature of this emergence should be substrate-independent: appearing in learning systems (MARL agents), non-learning systems (ant colonies), and token-distributional systems (language models) using the same formal structure.

This has not, to our knowledge, been tested this way before in public. The study is ongoing. The findings stand. The community is invited to reproduce, challenge, and extend them.

---

## Current Status: Confirmatory Phase Complete — Post-Confirmatory Expanding

**As of 2026-03-08. All five confirmatory propositions resolved. ~755 total runs completed. Experiment 14 (coupling-window characterization) now queued as next priority.**

### Confirmatory Scorecard

| Prop | Prediction | Key Result | Status |
|---|---|---|---|
| **P1** | Interrogative emergence ≥5% of seeds | 90% cryst. (P1) vs 0% (P0) | ✅ CONFIRMED |
| **P2** | r(query_cost, query_rate) < −0.70 | r=−0.7047, p=2×10⁻¹⁰ | ✅ CONFIRMED |
| **P3** | Hysteresis in weight space | 8/10 seeds maintained post-freeze | ✅ CONFIRMED |
| **P4** | Architecture independence | ANOVA F=3.30, p=0.0796 | ✅ CONFIRMED |
| **P5** | Coordination advantage ≥1.25× ROI | ROI 1.44× ✅ / survival d=0.11 ❌ | ⚠️ PARTIAL (exploratory) |

### Ant Track Scorecard

| Hyp | Prediction | Key Result | Status |
|---|---|---|---|
| **A-H1** | Phase transition in crystallization | Peak shifted δ=0.20 (predicted 0.10) | ⚠️ PARTIAL |
| **A-H2** | SCI co-located with cryst. peak | SCI inversely correlated, r=−0.96 | ❌ NOT CONFIRMED* |
| **A-H3** | Throughput plateau | 0.378× at δ=0.20, flat to 0.30 | ✅ CONFIRMED |
| **B-H1** | Hysteresis present | 30/30 seeds, p<10⁻⁸ | ✅ CONFIRMED |
| **B-H2** | Path-dependence ratio > 1.3 | Ratio = 1.68 | ✅ CONFIRMED |
| **B-H3** | Hysteresis magnitude ≥ 1 | Mean = 1.0, sd = 0.0 | ✅ CONFIRMED (narrative) |
| **C-H1** | SCI monotone in τ | All adjacent pairs separated | ✅ CONFIRMED |
| **C-H2** | SCI(τ=20) ∈ (0.50, 0.90) | Actual = 0.0033 | ❌ NOT EVALUABLE† |
| **C-H3** | Knee in SCI curve | Log-linear, no knee | ❌ NOT SUPPORTED |

*A-H2 inversion is likely a measurement artifact: SCI is τ-dependent. Fixing τ=20 across conditions with very different event frequencies causes inversion. The underlying co-location hypothesis is not refuted — the metric design has a limitation that is disclosed here and will be addressed in Experiment 14.

†C-H2 threshold was written by analogy with QRC (0.81–0.97) without scale adjustment — approximately 150× too high. Classified as a preregistration quality failure. Disclosed.

---

## What the Confirmed Findings Mean

**P1 — 90% vs 0% crystallization** is not a marginal result. It is a clean binary separation across 75 runs and all tested architectures. Under differentiated communication cost, interrogative protocols emerge. Without it, they do not. This is robust and mandatory, not fragile.

**P2 — r=−0.7047, p=2×10⁻¹⁰** with monotone dose-response spanning 20× in query rate (0.2856 → 0.0142). The logistic tax sweep pins the critical emergence threshold at q≈0.91, transition band [0.13, 1.70]. Below this, crystallization is rare; above it, robust and dose-dependent.

**P3 — Hysteresis in weight space.** Protocol structure is a stable attractor, not a sustained equilibrium. 8/10 crystallized seeds maintained their protocol structure after cost pressure was relaxed and training frozen. The two failures differ: one seed fully dissolved (entropy above 0.95); one persisted marginally below threshold. Different failure modes, both disclosed.

**P4 — Architecture independence.** What matters is the functional broker role, not the architecture filling it. Ablation confirms: freezing the broker agent's type_head to DECLARE drops crystallization from 100% → 40% and delays onset from ~25 → 82.5 epochs. The architecture type is not the critical variable. The role is.

**Ant bridge hysteresis (B-H1, B-H2)** — 30/30 seeds, zero variance. Dissolution gap consistently below formation gap; bridge size ratio 1.68 on ramp-down vs ramp-up. The zero variance is a simulation mechanics property (hardcoded min_jump_size, deterministic leave_patience coupling), not a biological claim. What the result demonstrates: hysteresis is mathematically necessary given mechanics that are a reasonable abstraction of ant behavior. Real colonies would show variance. The result supports the *existence* of hysteresis in the biological substrate.

**Counter-wave discrimination** — DECLARE spikes in pilot data are boundary artifacts, not pragmatic signaling or reward exploitation. H2 (phase-reset) is the proximate cause: removing the episode boundary removes the spikes (Exp3). H3 (pressure) is a modulating condition: sustained pressure amplifies magnitude but does not create the trigger. These operate at different levels and are compatible.

---

## What Was Not Confirmed — And Why It Matters

**P5** showed correct direction but small effect (d=0.11, p=0.273, n=30). Energy ROI cleared the criterion at 1.44×; survival rate differential did not reach significance. The original n=15 result (mean diff +0.053) inflated to n=30 (+0.023). This is valid exploratory science. Preregistration discipline caught the inflation. Reported transparently.

**A-H2 SCI inversion** — the metric has a τ-dependency that was not anticipated in the preregistration. This is a finding about measurement design, not a refutation of the underlying co-location hypothesis. Experiment 14 will address this directly.

**Two preregistration quality failures** are explicitly disclosed:
- C-H2 threshold ~150× off due to scale analogy error
- B-H3 stat plan inconsistency (narrative threshold updated, stat plan not updated)

These are disclosed because transparency is the operating principle. The failures are in the measurement design, not in the phenomenon.

---

## Repository Structure

```
backend/
  app/           FastAPI API layer (runs, reports, loom, control endpoints)
  simulation/    MARL engine (protocols, agents, environment, metrics)
  run_baseline.py
  run_inquiry.py

frontend/        React + TypeScript UI
  src/pages/     Lab Notebook (Dashboard · History · Compare · Reports)
                 Neural Loom (Control Deck · PCA · QRC · ROI)

docs/
  preregistration.md              Locked preregistration (SHA-256 verified)
  preregistration-ant-modules-addendum-2026-03-01.md
  results-marl.md
  results-ant-modules.md
  theory/
```

---

## Protocols

| Protocol | Description | Command |
|---|---|---|
| P0 | Baseline — flat energy tax, no signal types | `python run_baseline.py --epochs 500` |
| P1 | Interrogative Emergence — Gumbel-Softmax type head, variable costs | `python run_inquiry.py --epochs 500` |

---

## Quick Start

```bash
# Backend (Python 3.11+)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload

# Frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Pilot Data

Run 11 (seed=42, 500 epochs, Protocol 1) is included as pilot data in
`frontend/public/run_11_extended_report.json`. Load it in the Neural Loom
to explore the three crystallisation waves and QRC lock-in at E496.

This run is **excluded from confirmatory hypothesis testing** per the preregistration.

---

## Next: Experiment 14 — Coupling-Window Characterization (MARL)

`run_exp14_coupling_window.py` — 135 runs — is the next queued experiment.

This is the MARL analogue to Ant Experiment C, which characterized how the SCI measurement window τ affects the coupling signature in the ant system. The ant result showed that SCI is τ-dependent in a way that was not anticipated in the preregistration: fixing τ across conditions with very different event frequencies produces an inversion artifact.

Experiment 14 will test whether the same τ-dependence appears in the MARL system. Two outcomes are both informative:

- **If MARL shows the same τ-dependence:** this creates a principled cross-substrate argument that the coupling-window limitation is a property of the measurement framework, not the underlying phenomenon — and that the same measurement design issue appears identically across substrates. This would strengthen the substrate-independence claim.
- **If MARL does not show τ-dependence:** this is an asymmetry between the two substrates that requires explanation. It would constrain the substrate-independence claim and open a productive line of investigation into what differs between the two systems at the measurement level.

Either outcome advances the theory. This is what the next phase of the study will produce.

---

## Full Experiment Queue (Post-Confirmatory)

| # | Script | Runs | Description | Priority |
|---|---|---|---|---|
| 1 | `run_exp14_coupling_window.py` | 135 | MARL coupling-window characterization | **NEXT** |
| 2 | `run_exp3_metastability.py` | 45 | Near-threshold stability characterization | High |
| 3 | `run_exp4_noise.py` | 120 | Observation noise robustness | Medium |
| 4 | `run_exp7_topology.py` | 45 | Communication graph topology effects | Medium |
| 5 | `run_exp8_memory_depth.py` | 75 | RNN hidden state depth sensitivity | Medium |
| 6 | `run_exp9_observability.py` | 75 | Partial observability effects | Medium |
| 7 | `run_exp11_saturation.py` | 60 | High-load saturation behavior | Medium |
| 8 | `run_exp12_irreversibility.py` | 15 | Cost irreversibility effects | Medium |
| 9 | `run_exp13_redistribution.py` | 75 | Reward redistribution under crystallization | Medium |
| 10 | `run_exp15_ablation.py` | 75 | Full ablation battery | Medium |

**Total queued: 720 runs** (Exp 1 tax sweep complete; removed from queue)

---

## This Is an Ongoing Study

This repository will remain active and open as the study continues. Results will be added as experiments complete. The preregistration is locked and SHA-256 verified; any post-confirmatory work is labeled explicitly as exploratory.

The community is invited to:
- **Reproduce** the confirmatory campaign using the data and harness provided
- **Challenge** the findings — the falsification criteria are documented; use them
- **Extend** the experimental queue — issues are open
- **Cite** via the Zenodo DOI: [10.5281/zenodo.18738379](https://doi.org/10.5281/zenodo.18738379)

If you are aware of prior published work that has tested substrate-independent interrogative emergence in this way — across learning and non-learning systems, with preregistered hypotheses and disclosed failures — please open an issue. The claim that this has not been done publicly before is held with appropriate uncertainty. Correction is welcome.

---

## Theory

The Δ-Variable Theory proposes that interrogative structures emerge as mathematical necessities when:
1. Systems must coordinate under resource constraints
2. Information is asymmetrically distributed
3. Communication carries differential cost

Under these conditions, a QUERY/RESPOND protocol is the optimal solution. The theory predicts this emergence is substrate-independent — appearing in learning agents, stigmergic biological systems, and statistical language models through the same formal signature.

**External validation:** AnnA (Puchtel, 2026) served as an independent examination frame during experimental development. AnnA's diagnostic questions — where does pressure accumulate, does structure persist after strain, is coherence structural or reactive — were answered by the results without having been designed into the harness. This convergence is noted, but AnnA does not ground the Δ-variable claim. The preregistration reflects the independent theoretical basis.

Related work: Busemeyer & Bruza (quantum cognition formalisms), Friston (Free Energy Principle), Shannon (entropy as information).
---

## Original Development Repository

[Cross-Origin-Constraint](https://github.com/btisler-DS/cross-origin-constraint) — archived development history and Run 11 pilot artifacts.

## About

Experimental harness for the Δ-Variable Theory of Interrogative Emergence — multi-agent MARL system with Protocol registry, Lab Notebook, and Neural Loom visualizer.

**Author:** Bruce Tisler | [quantuminquiry.org](https://quantuminquiry.org) | ORCID: [0009-0009-6344-5334](https://orcid.org/0009-0009-6344-5334)

**License:** CC BY 4.0 — use it, build on it, cite it.
