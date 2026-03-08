# Preregistration v2: Post-Confirmatory Phase
## The Δ-Variable Theory of Interrogative Emergence

**Date:** 2026-03-08
**Author:** Bruce Tisler | quantuminquiry.org | ORCID: 0009-0009-6344-5334
**Confirmatory DOI:** [10.5281/zenodo.18738379](https://doi.org/10.5281/zenodo.18738379)
**v2 DOI:** [10.5281/zenodo.18912837](https://doi.org/10.5281/zenodo.18912837)
**Status:** Confirmatory phase closed. Post-confirmatory phase open.

---

## Part 1: Closing Statement on the Confirmatory Phase

The confirmatory experimental campaign is closed as of 2026-03-08. All five MARL propositions and all applicable ant-track hypotheses have been resolved. This document serves as the formal closing record and the preregistration for the post-confirmatory research program.

### 1.1 Confirmatory Scorecard — Final

#### MARL Propositions

| Prop | Prediction | Key Result | Status |
|---|---|---|---|
| P1 | Interrogative emergence ≥5% of seeds | 90% crystallization (P1) vs 0% (P0) | ✅ CONFIRMED |
| P2 | r(query_cost, query_rate) < −0.70, p < 0.01 | r=−0.7047, p=2×10⁻¹⁰ | ✅ CONFIRMED |
| P3 | Hysteresis in weight space | 8/10 seeds maintained post-freeze | ✅ CONFIRMED |
| P4 | Architecture independence | ANOVA F=3.30, p=0.0796 | ✅ CONFIRMED |
| P5 | Coordination advantage ≥1.25× ROI | ROI 1.44× ✅ / survival d=0.11, p=0.273 ❌ | ⚠️ PARTIAL — EXPLORATORY |

#### Ant-Track Hypotheses

| Hyp | Prediction | Key Result | Status |
|---|---|---|---|
| A-H1 | Phase transition in crystallization rate | Peak at δ=0.20, not preregistered δ=0.10 | ⚠️ PARTIAL |
| A-H2 | SCI co-located with crystallization peak | SCI inversely correlated, r=−0.96 | ❌ NOT CONFIRMED* |
| A-H3 | Throughput plateau | 0.378× at δ=0.20, flat to δ=0.30 | ✅ CONFIRMED |
| B-H1 | Hysteresis present | 30/30 seeds, p<10⁻⁸ | ✅ CONFIRMED |
| B-H2 | Path-dependence ratio > 1.3 | Ratio = 1.68 | ✅ CONFIRMED |
| B-H3 | Hysteresis magnitude ≥ 1 | Mean = 1.0, sd = 0.0 | ✅ CONFIRMED (narrative only†) |
| C-H1 | SCI monotone in τ | All adjacent pairs separated, p < 0.01 | ✅ CONFIRMED |
| C-H2 | SCI(τ=20) ∈ (0.50, 0.90) | Actual = 0.0033 | ❌ NOT EVALUABLE‡ |
| C-H3 | Characteristic knee in SCI curve | Log-linear, no knee | ❌ NOT SUPPORTED |

*A-H2 failure is attributed to a measurement design limitation: SCI is τ-dependent. Fixing τ=20 across conditions with very different event frequencies produces an inversion artifact. The underlying co-location hypothesis is not considered refuted. Experiment 14 (MARL coupling-window) is designed to address this directly.

†B-H3 stat plan inconsistency: narrative threshold (≥1) was updated before lock but the corresponding statistical test was not updated. Result is reported against the narrative criterion only. Inconsistency disclosed.

‡C-H2 preregistration quality failure: threshold of SCI(τ=20) ∈ (0.50, 0.90) was written by analogy with QRC (0.81–0.97) without scale adjustment. Actual SCI values are approximately 150× smaller than the threshold range. This is a preregistration design error, not a theory failure. Classified as not evaluable and excluded from the confirmatory record.

### 1.2 Post-Confirmatory Investigations (Closed)

The following investigations were conducted after the confirmatory campaign and before this v2 preregistration. All are labeled exploratory.

| Investigation | Key Result | Status |
|---|---|---|
| P2 rerun (per_agent_types field) | r=−0.7047, p=2×10⁻¹⁰ | CLOSED — confirmed P2 with correct metric |
| P5 rerun (survival diff, n=30) | d=0.11, p=0.273 — not significant | CLOSED — reported as exploratory |
| Counter-wave discrimination | H2 (phase-reset) supported; H3 modulating | CLOSED |
| Agent C broker ablation | Crystallization 100%→40%; onset +57 epochs | CLOSED |
| Experiment 1 tax sweep (logistic) | Critical threshold q=0.9114, band [0.13, 1.70] | CLOSED |

### 1.3 Disclosed Failures and Corrections

Two preregistration quality failures are formally disclosed:

**C-H2 threshold error:** The SCI threshold for Experiment C Hypothesis 2 was set by analogy with QRC metrics without adjusting for scale. The pilot SCI value (0.0036) was available at preregistration lock and should have been used to calibrate the threshold. It was not. This is a researcher error in the preregistration design. The hypothesis is classified as not evaluable and is excluded from the confirmatory record. It does not count for or against the theory.

**B-H3 stat plan inconsistency:** The narrative threshold for bridge hysteresis magnitude was updated to ≥1 before lock, but the corresponding one-sample t-test null hypothesis (vs. null=2) was not updated. The observed result (mean=1.0, sd=0.0) satisfies the narrative threshold trivially but cannot be evaluated against the original statistical null. Reported against narrative criterion only. Inconsistency disclosed.

These failures are reported here in full because transparency is a condition of the research program, not an option. A preregistration that discloses its own errors is more credible than one that reports only its successes.

---

## Part 2: Theoretical Update

### 2.1 What the Confirmatory Phase Established

The confirmatory phase establishes the following with sufficient evidence to proceed:

1. **Interrogative emergence is structurally necessary under differentiated cost.** 90% vs 0% crystallization is a clean causal demonstration. The presence of informational asymmetry with differentiated type costs is sufficient to mandate query-response protocol emergence.

2. **The cost-emergence relationship is precise and quantifiable.** The critical threshold is q≈0.91 (logistic fit). Below this, crystallization is rare. Above it, robust and dose-dependent. This is a quantitative prediction the theory now generates.

3. **Protocol structures are stable attractors in weight space, not sustained equilibria.** Once crystallized, protocols resist destabilization when cost pressure is relaxed. This is hysteresis at the computational level.

4. **The functional broker role — not the architecture — is the critical variable for crystallization.** Removing the broker function drops crystallization from 100% to 40% and delays onset by ~58 epochs. Swapping architectures in the broker role does not significantly affect the outcome.

5. **Hysteresis appears in non-learning stigmergic systems under analogous constraints.** The ant bridge result (30/30, zero variance, ratio 1.68) demonstrates that path-dependence is mathematically necessary given mechanics that abstract reasonable biological behavior. This supports the substrate-independence claim.

### 2.2 What Remains Open

The following theoretical questions are not resolved by the confirmatory phase and motivate the post-confirmatory program:

- **The SCI metric is τ-dependent.** Whether this τ-dependence is symmetric across MARL and ant substrates is unknown. If symmetric, it is a measurement design property. If asymmetric, it is a theoretical finding about the substrates themselves.

- **The coordination advantage (P5) is present but small.** The energy ROI criterion is met; the survival rate differential is not significant. Whether a larger n or a different task structure would reveal a more robust advantage is open.

- **Near-threshold behavior is uncharacterized.** The wide crystallization onset variance (SD ~78 epochs across conditions) and the cluster of failures in low_pressure suggest metastability in the transition zone. Whether seeds eventually crystallize past epoch 500 under sustained low pressure — a slow escape from a metastable state rather than a structural failure — is not yet known.

- **Substrate independence has been tested across two substrate types.** The claim requires a broader test. Additional substrates (cellular automata, immune system models, economic coordination games) remain untested.

---

## Part 3: Post-Confirmatory Research Program

All work from this point is explicitly labeled **EXPLORATORY** unless a new confirmatory preregistration is filed for a specific experiment. The distinction between confirmatory and exploratory work will be maintained in all commits, reports, and publications.

### 3.1 Experiment 14 — MARL Coupling-Window Characterization (PRIORITY)

**Script:** `run_exp14_coupling_window.py`
**Runs:** 135
**Status:** Queued — NEXT

**Motivation:** Ant Experiment C revealed that the SCI metric is τ-dependent in a way that was not anticipated. The Stigmergic Coupling Index measures the probability that a Δ-event is resolved within a fixed window τ. When τ is fixed and event frequency varies across conditions, the metric conflates event resolution rate with event frequency — producing the inversion observed in A-H2. Experiment 14 tests whether the same τ-dependence appears in the MARL system using an analogous coupling-window metric.

**Two informative outcomes:**

- *If MARL shows τ-dependence matching the ant system:* The limitation is a property of the measurement framework, not the underlying phenomenon. The same design constraint appears identically across substrates — which is itself a substrate-independence finding at the measurement level. Provides a principled basis for redesigning the SCI metric.

- *If MARL does not show τ-dependence:* This is an asymmetry between the two substrates that requires explanation. It constrains the substrate-independence claim and opens a new line of investigation into what differs between the two systems at the measurement level.

**Exploratory hypotheses (not preregistered — labeled exploratory):**

- E14-H1: MARL QRC will show monotone increase with coupling window τ, paralleling Ant C-H1.
- E14-H2: The τ-dependence slope will not differ significantly between MARL and ant substrates, supporting symmetric measurement constraint.
- E14-H3: A characteristic coupling-window value will emerge in MARL corresponding to the mean QRC lock-in latency.

### 3.2 Full Post-Confirmatory Queue

| # | Script | Runs | Description | Priority |
|---|---|---|---|---|
| 1 | `run_exp14_coupling_window.py` | 135 | MARL coupling-window characterization | **NEXT** |
| 2 | `run_exp3_metastability.py` | 45 | Near-threshold stability — slow escape vs structural failure | High |
| 3 | `run_exp4_noise.py` | 120 | Observation noise robustness | Medium |
| 4 | `run_exp7_topology.py` | 45 | Communication graph topology effects | Medium |
| 5 | `run_exp8_memory_depth.py` | 75 | RNN hidden state depth sensitivity | Medium |
| 6 | `run_exp9_observability.py` | 75 | Partial observability effects | Medium |
| 7 | `run_exp11_saturation.py` | 60 | High-load saturation behavior | Medium |
| 8 | `run_exp12_irreversibility.py` | 15 | Cost irreversibility effects | Medium |
| 9 | `run_exp13_redistribution.py` | 75 | Reward redistribution under crystallization | Medium |
| 10 | `run_exp15_ablation.py` | 75 | Full ablation battery | Medium |

**Total queued: 720 runs**

### 3.3 Operating Principles for the Post-Confirmatory Phase

1. **Exploratory is not lesser.** Exploratory work is how the next confirmatory hypotheses are generated. It is labeled honestly, not apologetically.

2. **All results reported.** Null results, failures, and unexpected findings are reported in the same detail as confirmations. The research record is complete or it is not a research record.

3. **Preregistration quality improves.** The two quality failures from v1 identified specific failure modes: threshold calibration without scale adjustment, and narrative/statistical plan inconsistency. Both are correctable. Future preregistrations will include explicit scale calibration checks and paired narrative/statistical threshold verification.

4. **Community engagement is active.** Reproduction attempts, challenges to the findings, and proposed extensions are welcomed via GitHub Issues. The falsification criteria are documented. Use them.

5. **The study does not close.** The Δ-Variable Theory generates predictions across substrates that have not yet been tested. The confirmatory phase closed one chapter. The research program is ongoing indefinitely.

---

## Part 4: Version History

| Version | Date | Description |
|---|---|---|
| v1 (original) | 2026-02-23 | Confirmatory preregistration locked — DOI: 10.5281/zenodo.18738379 |
| v2 (this document) | 2026-03-08 | Confirmatory phase closed. Full scorecard. Quality failures disclosed. Post-confirmatory phase opened. Experiment 14 queued. — DOI: 10.5281/zenodo.18912837 |

---

*This document will be submitted to Zenodo as a versioned update to the original preregistration record. The v1 document remains locked and unchanged. This v2 addendum is the closing record of the confirmatory phase and the opening record of the post-confirmatory phase.*

*Bruce Tisler | quantuminquiry.org | 2026-03-08*

**Preregistration Hash**: SHA-256: 8c31d5c54c689215aaacde856e60d79175bc050cdb2bb6e076f78b4205e953fb
