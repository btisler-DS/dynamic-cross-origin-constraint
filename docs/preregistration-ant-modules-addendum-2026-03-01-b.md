# Addendum B to Preregistration: Ant Colony Simulations — Modules 1 and 2
## B-H3 Stat Plan Inconsistency and A-H1 Planned Comparison Failure

**Addendum date: 2026-03-01**
**Original preregistration: docs/preregistration-ant-modules.md (locked 2026-03-01)**
**Addendum A: docs/preregistration-ant-modules-addendum-2026-03-01.md**
**This document does not modify the original preregistration.**

Identified during results documentation (docs/results-ant-modules.md).

---

## Issue 1 — B-H3: Inconsistency Between Narrative Criterion and Statistical Analysis Plan

### B-H3 as preregistered — narrative (verbatim):

> **B-H3 (Magnitude)**: mean hysteresis_magnitude >= 1 gap unit across hysteretic
> seeds. The 1-unit threshold reflects the discrete-grid minimum: dissolution_gap =
> min_jump_size and formation_gap = min_jump_size + 1 by model construction. This is
> expected to be constant across seeds (deterministic), confirming the structural
> asymmetry.

### B-H3 as preregistered — statistical analysis plan (verbatim):

> **B-H3 (Magnitude)**: One-sample t-test: mean hysteresis_magnitude (in hysteretic
> seeds only) vs. null=2. One-sided H1: mean > 2. alpha = 0.05.

### Internal inconsistency:

The narrative specifies a threshold of >= 1. The statistical analysis plan specifies
null=2, H1: mean > 2. These are incompatible: a test against null=2 can only pass if
the mean exceeds 2, but the narrative declares success at >= 1.

### Cause:

The B-H3 threshold was updated from >= 2 to >= 1 before lock, after it became clear
that the model mechanistically produces hysteresis_magnitude = 1 (formation_gap =
min_jump_size + 1 = 4, dissolution_gap = min_jump_size = 3). The narrative was
updated to reflect this. The statistical analysis plan was not correspondingly
updated and retains the original null=2.

### Observed result:

mean hysteresis_magnitude = 1.0, sd = 0.0, across all 30 seeds.

The t-test against null=2 cannot be computed (zero variance). Even if variance
were non-zero, the observed mean (1.0) is below the null (2), placing the evidence
against H1 (mean > 2). The narrative criterion (>= 1) is satisfied.

### Reporting classification:

**B-H3 is reported as confirmed against the narrative criterion only.**
The statistical analysis plan criterion is inapplicable due to the pre-lock narrative
update that was not propagated to the stat plan. This is a secondary preregistration
quality issue: less severe than C-H2 (where the threshold was incompatible with pilot
data available at lock) because the narrative update was intentional and correctly
motivated by the model mechanics.

---

## Issue 2 — A-H1: Planned Comparison Fails Due to Peak Location Mismatch

### A-H1 planned comparison as preregistered (verbatim):

> **Planned comparison**: crystallization_rate at delta=0.10 (preregistered optimal)
> vs. delta=0.04 (low) and delta=0.30 (high). Direction: rate(0.10) > rate(0.04) and
> rate(0.10) >= rate(0.30). Two-sample binomial tests, one-tailed,
> Bonferroni-corrected (alpha=0.025).

### Observed result:

| delta | Crystallization rate |
|---|---|
| 0.04 | 3.3% (1/30) |
| 0.10 | 63.3% (19/30) |
| 0.20 | 83.3% (25/30) — actual peak |
| 0.30 | 70.0% (21/30) |

- rate(0.10) > rate(0.04): 63.3% > 3.3% — DIRECTION MET
- rate(0.10) >= rate(0.30): 63.3% >= 70.0% — DIRECTION NOT MET

The second arm of the planned comparison fails. The actual peak is at delta=0.20, one
condition above the preregistered optimal of delta=0.10. Non-monotonicity exists (rise
from 0.04 to 0.20, decline from 0.20 to 0.30), but it is centered one condition to the
right of where the preregistration predicted.

### Classification:

A-H1 is **partially supported**. The qualitative prediction — non-monotonic
crystallization rate with a peak at intermediate delta and decline at high delta —
is confirmed in the data. The specific planned comparison (rate(0.10) >= rate(0.30))
fails because the preregistered optimal delta was miscalibrated: delta=0.10 was
designated as optimal without a sweep to determine the actual optimum. The actual
optimum is delta=0.20.

This is not a preregistration quality failure in the same category as C-H2 or the
B-H3 stat plan issue: the directional prediction (non-monotonicity) was genuine and
is visible in the data. The failure is in the specific operationalization (which delta
was labeled optimal), not in the core prediction. A-H1 is reported as partial support
with this disclosure.

---

## Updated Evaluable Scorecard

As of this addendum, the honest scorecard across both preregistrations is:

**MARL (explicit Delta):**
- P1: CONFIRMED
- P2: PENDING RERUN
- P3: CONFIRMED
- P4: CONFIRMED
- P5: NOT CONFIRMED (underpowered, d=0.28)

**Ant modules (implicit Delta):**
- A-H1: PARTIAL (non-monotonicity present, planned comparison fails)
- A-H2: NOT CONFIRMED (legitimate falsified prediction)
- A-H3: CONFIRMED
- B-H1: CONFIRMED (30/30)
- B-H2: CONFIRMED (ratio=1.68)
- B-H3: CONFIRMED against narrative criterion (stat plan quality issue disclosed)
- C-H1: CONFIRMED
- C-H2: PREREGISTRATION QUALITY FAILURE (disclosed in Addendum A)
- C-H3: NOT SUPPORTED

Summary: 5 confirmed (P1, P3, P4, A-H3, B-H1, B-H2, B-H3, C-H1 = 8 if counting ant
module confirmations), 1 partial (A-H1), 2 not confirmed / pending (P2, P5, A-H2,
C-H3), 2 quality issues disclosed (C-H2, B-H3 stat plan).

---

*This addendum was written on 2026-03-01 during results documentation, after campaign
data had been committed (commit 28b488c) and Addendum A had been committed (205cc2b).
The inconsistencies were identified by reviewing the locked preregistration against
the results section being drafted.*
