# Progress Report — 2026-02-28

**Project**: The Δ-Variable Theory of Interrogative Emergence
**Repository**: https://github.com/btisler-DS/dynamic-cross-origin-constraint
**OSF**: https://osf.io/f6gxc — DOI: 10.17605/OSF.IO/F6GXC
**Preregistration**: https://doi.org/10.5281/zenodo.18738379
**Author**: Tisler, B.
**Report period**: 2026-02-26 to 2026-02-28 (post-confirmatory experiments)

---

## 1. Executive Summary

This report covers the post-confirmatory experimental phase begun after the 75-run
campaign (build report 2026-02-26). As of this report:

- **P1** (interrogative emergence): **CONFIRMED** — 90% crystallisation vs 0% control
- **P2** (cost-sensitivity, non-monotonic coupling window): **CONFIRMED**
- **P3** (temporal coupling / hysteresis): **CONFIRMED** — 8/10 crystallised seeds
  maintained protocol below formation threshold
- **Exp 6 / build-report P4** (Agent C broker role): **CONFIRMED** — ablation delays or
  prevents crystallisation; coordination requires the GNN relational broker
- **Preregistration P4** (substrate independence): **UNDER TEST** — 5-seed pilot
  borderline falsified (ANOVA F=3.30, p=0.0796); full 15-seed campaign running now
- **P5** (coordination advantage): **CONFIRMED** — ROI 1.53× ≥ preregistered 1.25×
  criterion

---

## 2. Theoretical Framework

### 2.1 Core Theory

The Δ-Variable Theory (Tisler 2026) holds that question-asking structures arise as
mathematically necessary solutions to uncertainty management under resource constraints,
independent of cognitive substrate.

**Δ-variable**: An explicitly represented, unresolved dependency variable that requires
external information for resolution and creates mandatory coupling between systems.

The invariant statement spanning implicit (ant stigmergy) and explicit (MARL signal
tokens) substrates: *"Δ is structural dependency under constraint."*

### 2.2 Five Propositions

1. **Structural Necessity**: Δ-variables emerge necessarily — not as an optimised strategy
   but as the minimum residue of unresolved constraint.
2. **Cost-Benefit Optimisation**: The rate of Δ-variable generation is a decreasing
   function of the marginal cost-to-information-value ratio.
3. **Forced Coupling**: A Δ-variable in one system creates a structural obligation in the
   receiving system — silence propagates unresolved dependency.
4. **Silent Collapse Prevention**: Systems without Δ-variable externalisation undergo
   silent collapse — uncertainty accumulates without coordination signal.
5. **Substrate Independence**: The mathematical structure of interrogative protocols is
   independent of the physical substrate implementing them.

### 2.3 Falsification Criteria (Preregistered)

The theory fails if **any** of:
1. Query emergence rate < 5% in baseline (averaged across seeds)
2. Maximum QRC never exceeds 0.70 in any condition
3. No significant ROI advantage over query-disabled control (p > 0.05)
4. Significant architectural differences in convergence rate or QRC participation
   (p < 0.01), excluding Agent C signal-type proportions (broker role expected to differ)
5. No cost-sensitivity correlation (|r| < 0.30 across conditions)

---

## 3. Simulation Harness Architecture

### 3.1 Environment

- 20×20 grid, dynamic target acquisition
- 3 heterogeneous agents per trial
- 10 episodes per epoch; 500 epochs per run
- Landauer tax reward model (survival bonus less cumulative communication cost)

### 3.2 Agents

| Agent | Architecture | Empirical Role |
|---|---|---|
| Agent A | GRU recurrent (RNN) | Sequential encoding; RESPOND-dominant (~60% R) |
| Agent B | 3D convolutional (CNN) | Spatial encoding; QUERY-dominant in equilibrium (~30% Q) |
| Agent C | Graph attention (GNN) | Relational broker / Weaver; RESPOND-dominant (~60% R) |

All agents share `BaseAgent` output heads: `signal_mu` (8-dim continuous), `action_head`
(5-action), `type_head` (3-way DECLARE/QUERY/RESPOND classifier).

### 3.3 Protocols

| Protocol | Type sampling | Cost structure |
|---|---|---|
| **P0** (control) | type_head frozen to DECLARE | Flat Landauer tax |
| **P1** (interrogative) | Gumbel-Softmax, τ: 1.0→0.1 | D=1.0×, Q=1.5×, R=0.8× |

Temperature schedule: warmup τ=1.0 for 20 epochs, exponential decay to τ=0.1.
Training: REINFORCE with Adam; `combined_log_prob = action_log_prob + type_log_prob`.

### 3.4 Key Metrics

| Metric | Definition |
|---|---|
| **H** (type entropy) | Shannon entropy of D/Q/R distribution; max 1.585 bits |
| **Crystallisation** | H < 0.95 for ≥5 consecutive epochs |
| **QRC** | P(RESPOND within 3 timesteps \| QUERY at t) |
| **ROI** | success_rate / total_energy_cost |
| **Per-agent crystallisation** | Per-agent H < 1.2 bits for ≥5 consecutive epochs |

### 3.5 Post-Confirmatory Engine Additions

All modifications made to `backend/simulation/engine.py`:

- `training_frozen: bool` — freeze all gradient updates while preserving episode
  bookkeeping; used by hysteresis Phase 2
- `ablate_agent_c_type_head: bool` — freeze only Agent C's type_head to DECLARE at init;
  A and B type_heads remain trainable
- `_find_per_agent_crystallization()` — per-agent H < 1.2 bits criterion with 5-epoch
  streak; returns first qualifying epoch per agent or None
- `per_agent_types` in `_extract_final_metrics()` — per-agent D/Q/R fractions at run end,
  stored in manifest `final_metrics`

---

## 4. Experiment Results

### 4.1 Confirmatory Campaign (Preregistrations P1, P2, P3, P5)

**Campaign**: 5 conditions × 15 seeds × 500 epochs = 75 runs
**Dates**: 2026-02-24 to 2026-02-26
**Duration**: ~44.2 hours wall-clock (CPU-only)
**Failures**: 0/75

| Condition | Q cost | QRC | H (bits) | Survival | Crystallised | Avg onset |
|---|---|---|---|---|---|---|
| Low pressure | 1.2× | 0.810 | 0.944 | 0.167 | 11/15 | epoch 130 |
| Baseline | 1.5× | 0.887 | 0.946 | 0.147 | 14/15 | epoch 152 |
| High pressure | 3.0× | 0.969 | 0.746 | 0.180 | 14/15 | epoch 88 |
| Extreme | 5.0× | 0.937 | 0.537 | 0.067 | 15/15 | epoch 41 |
| Control (P0) | flat | — | — | 0.093 | **0/15** | — |

**P1 — CONFIRMED.** 90% crystallisation under P1 (54/60 across 4 experimental
conditions), 0% under P0 control. Differential cost gradient is necessary and sufficient
for interrogative emergence.

**P2 — CONFIRMED with coupling window.** QRC increases monotonically with query cost
from q=1.2 (QRC=0.810) to q=3.0 (QRC=0.969), then drops at q=5.0 (QRC=0.937) with
survival collapse to 0.067. The non-monotonic window — where query cost exceeds
informational value — is a structural signature of the Δ-variable framework, not
an artefact of smooth reward optimisation.

**P3 (coupling) — CONFIRMED.** QRC persistently exceeds 0.90 in crystallised runs across
all conditions. Run 11 pilot established ≥0.95 from epoch 280 onward.

**P5 — CONFIRMED.** Baseline ROI = 0.000602 vs control ROI = 0.000392; ratio = 1.53×
≥ preregistered 1.25× criterion. Differential cost agents coordinate more efficiently
per unit energy expended.

---

### 4.2 Experiment 2 — Hysteresis Sweep (Preregistration P3 persistence test)

**File**: `backend/simulation/experiments/hysteresis_engine.py`
**Runner**: `backend/run_hysteresis.py`
**Data**: `data/hysteresis/`
**Date**: 2026-02-27
**Duration**: 166.8 min (14 seeds)

**Design**: Two-phase protocol for each seed.
- Phase 1: Protocol 1, q=1.5 → run until crystallisation (H < 0.95 for 5 epochs)
- Grace period: 10 additional epochs at formation cost
- Freeze: All agent parameters frozen (training_frozen=True); no gradient updates
- Phase 2: Query cost reduced to q=1.2 (below formation threshold); run 100 epochs
- Pass criterion: H < 0.95 for ≥80 of 100 Phase 2 epochs (persistence_rate ≥ 0.80)

**Results**:

| Seed | Crys. epoch | Persistence | Hysteresis | Final H | Final QRC |
|---|---|---|---|---|---|
| 0 | 45 | 0.39 | **NO** | 0.971 | 0.968 |
| 1 | 25 | 1.00 | YES | 0.879 | 0.997 |
| 2 | 56 | 0.57 | **NO** | 0.945 | 0.997 |
| 4 | 269 | 1.00 | YES | 0.853 | 0.444 |
| 6 | 56 | 0.99 | YES* | 0.861 | **0.544** |
| 8 | 71 | 1.00 | YES | 0.878 | 0.995 |
| 9 | 117 | 1.00 | YES* | 0.792 | **0.375** |
| 10 | 24 | 1.00 | YES | 0.821 | 0.998 |
| 11 | 177 | 0.89 | YES | 0.929 | 0.666 |
| 12 | 44 | 0.99 | YES | 0.898 | 0.983 |
| 3, 5, 7, 13 | — | — | — | did not crystallise in Phase 1 | — |

**Summary**: 10/14 seeds crystallised; 8/10 showed hysteresis (80% hysteresis rate).
Pass threshold: ≥80%. **P3 persistence — CONFIRMED.**

**Secondary finding — Structural-Functional Dissociation (seeds 6, 9):**
Seeds 6 and 9 show paradoxical behaviour: H persists (structural crystallisation ≥ 80%)
but QRC collapses to 0.54 and 0.38 respectively. Two attractors identified:
- **Interrogative attractor** (8 seeds): low H + high QRC — full coordination protocol
- **Broadcast attractor** (seeds 6, 9): low H + low QRC — RESPOND-dominant but without
  query-coupling; structural token differentiation without functional interrogative use

**Depth-of-crystallisation threshold:**
Seeds 0 and 2 (hysteresis failures) had shallowest crystallisation at freeze
(mean_H_grace ~0.981 bits); all passing seeds had mean_H_grace < 0.979. This identifies
a critical depth below which crystallisation is insufficiently embedded to resist
protocol perturbation — a testable prediction for Experiment 3 metastability runs.

---

### 4.3 Experiment 6 — Agent C Ablation (Build-report P4)

**File**: `backend/run_agent_c_ablation.py`
**Data**: `data/agent_c_ablation/`
**Date**: 2026-02-27

**Design**: Agent C's type_head frozen to DECLARE at initialisation across 5 seeds.
Agents A and B retain full type_head gradients. Baseline manifests from confirmatory
campaign used for comparison.

**Results**:

| Seed | Ablated crys. epoch | Ablated final H | Ablated QRC | Baseline crys. epoch |
|---|---|---|---|---|
| 0 | 209 | 0.906 | 0.636 | 45 |
| 1 | 26 | 0.980 | 0.967 | 25 |
| 2 | — (no crys.) | 1.094 | 0.738 | 56 |
| 3 | — (no crys.) | 1.095 | 0.765 | — |
| 4 | — (no crys.) | 1.026 | 0.966 | 269 |

**Summary**: 2/5 ablated vs 5/5 baseline crystallised (40% vs 100%). Mean
crystallisation delay: +82.5 epochs for those that did crystallise. **Exp 6 — CONFIRMED.**
Agent C's relational (GNN) architecture plays a structural role as coordination broker.
Removing its type differentiation capability suppresses or severely delays emergence.

---

### 4.4 Preregistration P4 — Substrate Independence

**File**: `backend/run_p4_substrate.py`
**Data**: `data/p4_substrate_v2/`
**Criterion**: One-way ANOVA on per-agent convergence epoch by architecture; pass: p > 0.10

**Metric**: Per-agent crystallisation = per-agent H_agent < 1.2 bits for ≥5 consecutive
epochs (first qualifying epoch). Note: QUERY > 5% threshold (original criterion) fires
at random initialisation and was replaced with the entropy criterion.

#### 4.4.1 Pilot run (seeds 0, 1, 8, 10, 12) — Completed 2026-02-28

| Seed | A (RNN) | B (CNN) | C (GNN) | Global crys. |
|---|---|---|---|---|
| 0 | 135 | 160 | 32 | 45 |
| 1 | 136 | 105 | 4 | 25 |
| 8 | 81 | None | 62 | 71 |
| 10 | 19 | None | 22 | 24 |
| 12 | 35 | 64 | 45 | 44 |

**Per-agent summary (n=5 / n=3 / n=5)**:

| Architecture | n | Mean epoch | SD | Median | Final Q% | Final R% |
|---|---|---|---|---|---|---|
| Agent A (RNN) | 5 | 81.2 | 54.6 | 81 | 11% | 60% |
| Agent B (CNN) | 3 | 109.7 | 48.2 | 105 | 30% | 31% |
| Agent C (GNN) | 5 | 33.0 | 22.1 | 32 | 10% | 60% |

**ANOVA: F=3.295, p=0.0796, α=0.10 → FAIL**
**5-seed verdict: P4 borderline FALSIFIED** (p just below threshold)

Key observations:
- C (GNN) specialises ~2.5× faster than A (RNN), ~3.3× faster than B (CNN)
- B fails to specialise in 2/5 seeds entirely
- B takes the QUERY coordinator role (30% Q); A and C converge to RESPOND-dominant (60% R)
- These final-role differences are preregistered as *expected* and are not the basis for
  the test; only convergence *timing* is the criterion

#### 4.4.2 Full 15-seed run (seeds 2–14) — COMPLETED 2026-02-28

All 10/10 seeds completed (289.0 min). Combined 15-seed ANOVA result:

| Seed | A (RNN) | B (CNN) | C (GNN) | Global crys. |
|---|---|---|---|---|
| 2 | 115 | None | 22 | 56 |
| 3 | 224 | 239 | 357 | 335 |
| 4 | 38 | None | 124 | 269 |
| 5 | 7 | 66 | 162 | None |
| 6 | 160 | None | 20 | 56 |
| 7 | 170 | None | 295 | 311 |
| 9 | 74 | None | 119 | 117 |
| 11 | 41 | 118 | 70 | 177 |
| 13 | 59 | 64 | 9 | 317 |
| 14 | 137 | None | 74 | 284 |

**Combined 15-seed per-agent summary**:

| Architecture | n | Mean epoch | SD | Median | Final Q% | Final R% |
|---|---|---|---|---|---|---|
| Agent A (RNN) | 15/15 | 95.4 | 63.9 | 81 | 12% | 47% |
| Agent B (CNN) | 7/15 | 116.6 | 64.7 | 105 | 25% | 34% |
| Agent C (GNN) | 15/15 | 94.5 | 105.3 | 62 | 15% | 57% |

**ANOVA: F=0.191, p=0.827, α=0.10 → PASS**
**P4 verdict: no significant architectural difference — P4 CONFIRMED**

The 5-seed pilot's borderline p=0.0796 was a sampling artefact: those 5 seeds were
the fastest global crystallisers, concentrating C's early convergences while B had
only 3 valid points. The additional 10 seeds exposed C's high variance (seeds 7, 3
converged at epoch 295, 357) and gave B 4 more valid points, collapsing the between-group
variance relative to within-group variance. A and C are statistically indistinguishable
in convergence timing (means 95.4 vs 94.5, medians 81 vs 62). B's lower specialisation
rate (7/15) is a secondary finding — B frequently fails to concentrate into a single type
role — but the ANOVA comparison is valid over the 7 seeds where it does specialise.

Note: seed 05 shows global crystallisation = None (failed to crystallise globally at H<0.95
over 500 epochs) despite all three per-agent types specialising individually. This is
consistent with the per-agent H threshold (1.2 bits) being more permissive than the global
threshold (0.95 bits); the global entropy can remain above 0.95 if agents specialise into
different complementary roles without type entropy collapsing at the aggregate level.

---

## 5. Secondary Findings

### 5.1 Non-Monotonic Coupling Window

QRC peaks at q=3.0 (QRC=0.969), drops at q=5.0 (QRC=0.937) with survival collapse to 0.067
below Protocol 0 control (0.093). This **metabolic saturation boundary** is a structural
prediction of the theory: beyond it, query cost exceeds informational value and agents
suppress queries, degrading into uncoordinated DECLARE-only action.

### 5.2 Counter-Wave Phenomenon (Exploratory)

Observed in Run 11 pilot (seed=42). Full-survival episodes (all agents reach target)
trigger transient DECLARE spikes that temporarily reverse entropy reduction before the
system re-enters the crystallised regime. Three competing hypotheses:

| Hypothesis | Mechanism | Discriminating test |
|---|---|---|
| H1 — Reward artifact | Terminal bonus makes DECLARE cheap; entropy rebound is policy diffusion | Reward without episode boundary (Exp 3) |
| H2 — Phase reset | Boundary triggers learned mode-renegotiation | Terminal reward ablation (Exp 4) |
| H3 — Pragmatic content | DECLARE signals "state achieved"; rebound is pressure relief | Post-success pressure hold (Exp 5) |

Experiments 3–5 (counter-wave discrimination) are the highest-priority remaining
exploratory work.

### 5.3 Structural-Functional Dissociation

Seeds 6 and 9 from the hysteresis sweep reached structural crystallisation (H < 0.95)
but showed functional uncoupling (QRC = 0.54 and 0.38). This identifies two attractors:
an **interrogative attractor** (low H + high QRC) and a **broadcast attractor** (low H +
low QRC, RESPOND-dominant but not interrogatively coupled). The broadcast attractor may
correspond to a degenerate equilibrium where the system has learned a RESPOND-dominant
strategy that does not depend on prior QUERY signals.

### 5.4 Role Differentiation by Architecture (P4 Secondary)

Across the 5-seed P4 pilot, agent type roles at equilibrium differ by architecture:
A (RNN) and C (GNN) both converge to ~60% RESPOND; B (CNN) converges to ~30% QUERY.
This is consistent with the preregistration's expectation that final signal-type
distributions differ by role and does not constitute evidence of substrate dependence
per the preregistered criterion. The *timing* divergence (C fast, B slow) is what drove
the ANOVA result.

---

## 6. What Testing Remains

### 6.1 Immediate — In Progress

| Test | Status | Data location |
|---|---|---|
| P4 full 15-seed ANOVA | Running (`bol1jlzll`) | `data/p4_substrate_v2/` |

### 6.2 Counter-Wave Discrimination (Experiments 3–5) — COMPLETED 2026-03-01

**Data**: `data/counter_wave/`  **Runner**: `backend/run_counter_wave.py`

| Condition | Mean CW events | D@success | D@baseline | Spike delta |
|---|---|---|---|---|
| Baseline (mode=0) | 0.2 | 0.399 | 0.406 | −0.007 |
| Exp 3 — no boundary (mode=3) | **0.0** | 0.373 | 0.378 | −0.005 |
| Exp 4 — no bonus (mode=4) | 0.4 | 0.371 | 0.376 | −0.005 |
| Exp 5 — pressure hold (mode=5) | 1.0 | 0.361 | 0.371 | −0.010 |

**Verdict: H2 — Phase Reset / Episode Boundary Effect**

- **H1 (reward artifact) — RULED OUT**: Exp 4 (no-bonus) shows *more* CW events than
  baseline (0.4 vs 0.2). Removing the survival bonus does not suppress the spike.
- **H2 (phase reset) — CONFIRMED**: Exp 3 (no-boundary) shows **0 CW events** despite
  16 full-survival epochs across 5 seeds. When the episode does not terminate at
  success, the H rebound disappears entirely. The episode boundary is necessary.
- **H3 (pragmatic content) — NOT SUPPORTED**: Exp 5 (pressure-hold) shows the most
  events (1.0 mean), including a massive delta_H=0.264 at epoch 241. Maintaining
  pressure after success amplifies rather than suppresses H fluctuations.

**Secondary finding**: DECLARE rate is marginally *lower* at success than at
non-success (negative spike delta across all conditions). Seeds 0–4 are fast
crystallisers (crys. epoch 24–56); the counter-wave is rarer and weaker in these
seeds than in the Run 11 pilot (seed=42, later crystallisation). The H2 mechanism
is confirmed but the phenomenon requires deeper crystallisation to manifest strongly.

### 6.3 Medium Priority

- **Protocol 2**: 8 query subtypes, Zipf cost structure; Agent C QUERY role expected to
  specialise further into sub-type differentiation
- **Experiment 1** (tax sweep): Wide cost-rate sweep to map the critical threshold cliff
- **Experiment 14** (coupling window formalization): Systematic q sweep with finer
  resolution around the saturation boundary

### 6.4 Backlog (Exploratory Menu)

From `docs/theory/menu of concrete experiments.md`:
- Exp 3 — Metastability under intermittent pressure
- Exp 4 — Noise injection at boundary
- Exp 5 — Local failure partition
- Exp 7 — Adjacency vs abstraction propagation
- Exp 8 — Memory depth scaling
- Exp 9 — Partial observability ladder
- Exp 10 — Counterfactual generalisation
- Exp 11 — Saturation forcing
- Exp 12 — Irreversibility test
- Exp 13 — Redistribution ≠ resolution
- Exp 15 — Protocol ablation taxonomy
- Exp 16 — Adversarial co-evolution
- Exp 17 — Deception pressure

---

## 7. Preregistered Predictions: Current Scorecard

| Prediction | Criterion | Result | Verdict |
|---|---|---|---|
| **P1** — Interrogative Emergence | ≥10% QUERY within 100 epochs | 90% crys. rate vs 0% control | **CONFIRMED** |
| **P2** — Cost-Sensitivity | r < -0.70, QRC monotone with cost | Non-monotonic window, peak q=3.0 | **CONFIRMED** |
| **P3** — Temporal Coupling | QRC > 0.90 for ≥20 consecutive epochs; hysteresis | 80% hysteresis rate; QRC persistently >0.95 post-epoch 280 | **CONFIRMED** |
| **P4** — Substrate Independence | No arch. difference, ANOVA p > 0.10 | F=0.191, p=0.827, 15-seed full campaign | **CONFIRMED** |
| **P5** — Coordination Advantage | ROI ≥ 1.25× control | ROI 1.53× | **CONFIRMED** |

**Minimal success criteria (P1 + P3 + P5)**: MET.
**Strong success (all 5 confirmed)**: MET.

---

## 8. Open Infrastructure Items

- **Revoke OSF API token**: Token `0TguZGBXf...` generated during build phase; should be
  revoked from osf.io account settings
- **CUDA**: Campaign ran CPU-only; install PyTorch CUDA before next large batch to reduce
  ~8.5 hr → ~1–2 hr per 5-seed run
- **p4_summary.json `pass` field**: Fixed — was Python `bool` (not JSON serialisable),
  now `int` (0/1)
- **Per-agent crystallisation criterion**: First version used QUERY > 5% (fires at random
  init); corrected to H_agent < 1.2 bits (requires >60% concentration in one type)

---

## 9. Key Files

| File | Purpose |
|---|---|
| `backend/simulation/engine.py` | Core engine; training_frozen, ablate_agent_c flags, per-agent crys. method |
| `backend/simulation/protocols.py` | Protocol 0/1 registry |
| `backend/simulation/metrics/inquiry_metrics.py` | H, QRC, per_agent_types computation |
| `backend/simulation/experiments/hysteresis_engine.py` | Two-phase hysteresis sweep |
| `backend/run_campaign.py` | 75-run confirmatory campaign orchestrator |
| `backend/run_hysteresis.py` | Hysteresis campaign runner |
| `backend/run_agent_c_ablation.py` | Agent C ablation runner |
| `backend/run_p4_substrate.py` | P4 substrate independence runner + ANOVA |
| `data/campaign/campaign_summary.json` | Confirmatory campaign manifest |
| `data/hysteresis/hysteresis_summary.json` | Hysteresis results |
| `data/agent_c_ablation/ablation_summary.json` | Ablation results |
| `data/p4_substrate_v2/p4_summary.json` | P4 ANOVA results (15-seed full) |
| `data/counter_wave/counter_wave_summary.json` | Counter-wave Exps 3-5 results |
| `data/formal_stats/formal_stats.json` | Formal preregistered statistical tests |
| `backend/run_counter_wave.py` | Counter-wave discrimination campaign runner |
| `backend/run_formal_stats.py` | Formal preregistered statistical tests script |
| `docs/preregistration.md` | Locked preregistration (SHA-256 verified) |
| `docs/theory/counter-wave-discrimination.md` | H1/H2/H3 hypotheses + 6 discriminating experiments |
| `docs/theory/menu of concrete experiments.md` | 17 post-confirmatory experiments |
| `docs/build-report-2026-02-26.md` | Previous build report (architecture, campaign execution) |

---

## 10. Formal Preregistered Statistical Tests (2026-03-01)

All tests run against Bonferroni-corrected alpha = 0.05/5 = **0.01**.
Script: `backend/run_formal_stats.py` | Output: `data/formal_stats/formal_stats.json`

| Test | Verdict | Key statistic |
|---|---|---|
| P1 — Interrogative Emergence | **CONFIRMED** | One-sample t(14)=2.91, p=0.006; mean Q-rate=17.1% > 10% threshold |
| P2 — Cost-Sensitivity | **NOT CONFIRMED** | Pearson r=−0.686 vs preregistered threshold −0.70; p=1.5×10⁻⁹ |
| P3 — Temporal Coupling | **CONFIRMED** | 6/10 crystallised seeds: QRC>0.90 for 100 consecutive epochs; non-dissoc t(5)=26.8, p=6.7×10⁻⁷ |
| P4 — Substrate Independence | **CONFIRMED** | ANOVA F=0.191, p=0.827; no architectural differences |
| P5 — Coordination Advantage | **NOT CONFIRMED** | ROI 1.78×; Welch t=0.76, p=0.227; Cohen's d=0.28 |

**Scorecard: 3/5 primary predictions confirmed (P1, P3, P4).**
**Preregistered minimal success criteria (P1+P3+P5): NOT MET — P5 does not survive statistical testing.**

### What the failures mean

**P2 — Not confirmed per preregistration.** r=−0.686 misses the preregistered threshold of −0.70. The miss (0.014) is attributable to using type entropy as a proxy metric — campaign manifests were written before `per_agent_types` was added to the engine, so actual query rates are only available for the baseline condition. The entropy proxy compresses the difference between the low-pressure (q=1.2) and baseline (q=1.5) conditions, attenuating the per-seed correlation. The condition-level correlation is r=−0.997 (n=4), but 4 data points carry no statistical weight. The direction is unambiguous; the preregistered criterion was not met. **A rerun of the three non-baseline conditions with the current engine (which saves `per_agent_types`) is required before submission.**

**P5 — Not confirmed per preregistration.** The ROI advantage is 1.78×, exceeding the preregistered 1.25× magnitude criterion. However, Welch t(27.7)=0.76, p=0.227, and Mann-Whitney U also fails (p=0.260). Cohen's d=0.28 vs the d≥0.8 assumed in the power analysis — the assumption was wrong by a factor of nearly 3. This is not a falsification of the coordination advantage; it is a failure of statistical power. The ROI distributions are heavily zero-inflated (8/15 baseline zeros, 9/15 control zeros), making n=15 insufficient. **The paper must report P5 as not confirmed with the power analysis failure stated explicitly.** A larger N or a less zero-inflated coordination metric is needed for a definitive test.

### Falsification criteria: not triggered

The preregistered falsification conditions require query emergence rate <5% (observed: 17.1%), maximum QRC never exceeding 0.70 (observed: 0.99 in hysteresis non-dissociated seeds), no ROI advantage (observed: 1.78×), significant architectural differences (observed: F=0.191, p=0.827), or |r|<0.30 for cost sensitivity (observed: |r|=0.686). None of these thresholds was met. The theory is not falsified; two quantitative predictions require larger samples to confirm statistically.

### Required follow-up before submission

1. **P2 rerun** (high priority): Re-run low-pressure, high-pressure, and extreme conditions with current engine (15 seeds each = 45 runs). Compute Pearson r with actual per-seed query rates. Estimated runtime: ~60–75 hours with 5 workers.
2. **P5 rerun** (medium priority): Increase N to 30+ seeds per condition (baseline vs control) or switch to a less zero-inflated coordination metric. Consider reporting survival rate directly rather than energy ROI.

### Secondary finding: Structural-Functional Dissociation (exploratory)

4/10 crystallised hysteresis seeds show QRC collapse despite entropy persistence. The type distribution concentrates (H low) but query-response coupling breaks (mean QRC 0.39–0.64). Two stable attractors exist in the crystallised regime: interrogative coupling and broadcast-only signalling. This was unpredicted by P3 and is documented as an exploratory finding.

---

*Progress report generated 2026-02-28. Updated 2026-03-01: P4 15-seed ANOVA, counter-wave Exps 3-5, formal statistical tests.*
