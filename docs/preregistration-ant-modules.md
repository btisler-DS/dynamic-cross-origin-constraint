# Preregistration: Ant Colony Simulations — Modules 1 and 2
## Implicit Δ-Variable Theory: Stigmergic Coupling and Bridge Hysteresis

**Status: LOCKED — 2026-03-01**

*Companion to the primary preregistration (https://doi.org/10.5281/zenodo.18738379).*
*All parameters in this document are fixed before campaign runs begin.*
*Do not modify after lock date.*

---

## Scope

This preregistration covers two independent simulation modules that test
Δ-Variable Theory predictions in non-representational (stigmergic) systems:

- **Module 1 — Pheromone Trail Foraging**: Tests Experiments A (deposition-cost sweep)
  and C (coupling-window characterization) in an ant foraging colony model.
- **Module 2 — Bridge Formation**: Tests Experiment B (gap-size hysteresis) using a
  physically accurate bridge model derived from McCreery et al. (2022) and Reid et al. (2015).

Both modules test whether the structural signatures predicted by Δ-Variable Theory
(phase-like regime formation, hysteresis, non-monotonic coupling window) appear
in a system with **no internal representation, no symbolic signaling, no tokens**.

---

## Theoretical Framework

### Implicit vs. Explicit Δ

The primary preregistration operationalizes Δ-variables as *explicitly represented*
unresolved dependency variables in MARL agents (QUERY/RESPOND token protocols).

These modules test the same structural kernel in implicit systems:

> **Δ-kernel (substrate-independent)**: Capacity-bound dependency under partial
> observability that cannot be resolved locally.

**Implicit Δ in Module 1 (pheromone foraging)**:
- Δ-event: ant reaches a junction where pheromone gradient on the followed layer
  falls below decision threshold θ_decision — insufficient information for directional
  choice.
- Closure: gradient reinforced by returning foragers within τ steps, crossing
  θ_decision and enabling directional movement.
- Failure mode: persistent low-gradient stagnation — no reinforcement cycle,
  colony coordination breakdown.

**Implicit Δ in Module 2 (bridge formation)**:
- Δ-event: ant reaches gap edge with no traversable path (no bridge in place).
- Resolution mechanism: other ants lock into bridge position, restoring traversability.
- Hysteresis signature: bridge formation threshold (gap_size needed to form bridge) ≠
  bridge dissolution threshold (gap_size at which bridge dissolves) — structural residue
  without representational memory.

### Stigmergic Coupling Index (SCI)

The Module 1 analogue of QRC (Query-Response Coupling):

**SCI = P(gradient crosses θ_decision within τ steps | Δ-event at t)**

where:
- **Δ-event**: the followed-layer pheromone in the strictly-forward Moore neighborhood
  of ant *i* is below θ_decision at step *t*.
- **Closure**: within τ steps, the maximum pheromone in the same strictly-forward
  neighborhood crosses θ_decision (due to returning forager reinforcement).
- **τ (closure window)**: preregistered as 20 steps (see calibration below).
- **θ_decision (decision threshold)**: preregistered as 0.1213 (see calibration below).

SCI does **not** apply to Module 2. Module 2 metrics are bridge size,
formation_gap, dissolution_gap, hysteresis magnitude, and throughput.

### Literature Basis for Module 2

McCreery et al. (2022, *Nature Communications*) formalized the accumulator model
for army ant (Eciton hamatum) bridges:

- **Join rule**: tactile pressure from ants walking over a stationary ant triggers
  freezing. Ant remains locked as long as traffic continues above it.
- **Leave rule**: when bridge population exceeds equilibrium, the bridge sags. Ants
  experiencing reduced tension (slackness/low neighbor count) become more likely to leave.
- **Hysteresis**: the asymmetry between join (pressure-triggered) and leave
  (slackness-triggered) rules produces different formation and dissolution thresholds.
  McCreery et al. confirmed formation threshold ≠ dissolution threshold empirically.

Reid et al. (2015, *PNAS*) documented the equilibrium density:
- **0.51 ants/mm of gap** — the density at which bridge cost-benefit optimizes.
- Scaled to grid units as `n_equilibrium = round(0.51 × gap_size)`.

---

## Module 1 — Pheromone Trail Foraging

### Environment

| Parameter | Value | Notes |
|---|---|---|
| Grid | 50 × 50 | Toroidal: no |
| Nest | (0, 0) | Top-left |
| Food | (49, 49) | Bottom-right |
| n_ants | 100 | All start at nest, outbound mode |
| n_steps | 2000 | Per run |

### Pheromone Dynamics

**Cross-layer following** (standard ACO, prevents positive-feedback oscillation):
- Outbound ants (mode 0): deposit on layer 0 (outbound trail); follow layer 1 (return trail).
- Return ants (mode 1): deposit on layer 1 (return trail); follow layer 0 (outbound trail).

**Parallel deposit updates**: all deposits buffered, applied after all ants move each step.
This prevents within-step ordering artefacts.

**Evaporation**: applied each step after deposits: `pheromone *= (1 - epsilon)`.

### Movement Rule (Strictly-Forward Gradient)

For ant at position *(r, c)* with target *(r_t, c_t)*:

1. Compute `curr_dist = |r - r_t| + |c - c_t|` (Manhattan distance to target).
2. Identify strictly-forward neighbors: `{(nr, nc) : |nr - r_t| + |nc - c_t| < curr_dist}`.
3. Compute max pheromone on follow_layer across strictly-forward neighbors.
4. **If** max_fwd_phero ≥ θ_decision: gradient-follow (move to highest-pheromone
   strictly-forward neighbor).
5. **Else**: Δ-event; move probabilistically, weighted `∝ 1/(dist_to_target + 1)`
   across all neighbors (distance heuristic, not gradient-following).

Lateral moves (neighbors with distance = curr_dist) are excluded from gradient following
to prevent cross-trail oscillation.

### Locked Parameters (Calibrated Before Campaign)

**θ_decision = 0.1213**

Calibration method: pilot run (500 steps, δ=0.10, ε=0.01, seed=0, θ_working=1.0).
At end of pilot, sample combined pheromone field (layer 0 + layer 1) across all cells.
θ_decision = 25th percentile of non-zero cells. Rationale: 75% of explored cells are
above this threshold → ant can confidently follow gradient; 25% are below → Δ-event.

Pilot results: 1966/2500 cells non-zero; p25=0.1213, p50=0.3285, p75=0.7651, max=2.7011.

**τ = 20 steps** (SCI closure window)

Rationale: Δ-events arise at junctions where no forager has recently passed. The τ=20
window allows for one full circuit by a nearby forager at typical movement speed (diagonal
nest→food path ≈ 49 steps one-way; local reinforcement from a nearby ant should arrive
within 20 steps). This value is fixed before Experiment C runs; Exp C characterizes the
sensitivity of SCI to τ but does not alter the preregistered τ.

**Crystallization detection**:
- entropy_max = log2(50 × 50) = log2(2500) ≈ 11.29 bits
- entropy_threshold = 0.60 × entropy_max ≈ 6.77 bits
- entropy_streak = 5 consecutive steps
- Crystallization requires entropy to **first rise above threshold** (confirming
  exploration phase) before tracking descent below it. This prevents false positives
  at step 0 when all ants are clustered at the nest (H ≈ 1.6 bits < 6.77).

### Experiment A — Deposition-Cost Sweep

**Purpose**: Test whether SCI and crystallization exhibit phase-like regime formation
under variation of the primary stigmergic cost lever (deposition rate δ).

**Fixed**: ε=0.01, τ=20, θ_decision=0.1213, grid=50×50, n_ants=100, n_steps=2000.

**Variable**: δ ∈ {0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30} (7 levels).

**Seeds**: 30 per condition (seeds 0–29).

**Total runs**: 7 × 30 = 210 runs.

**Outcome variables** (per run):
1. Crystallization: yes/no, crystallization_epoch (step number; NaN if none).
2. SCI (proportion of Δ-events resolved within τ=20 steps).
3. Throughput (food deliveries per step, mean over last 500 steps).
4. Mean pheromone entropy (last 500 steps).

**Primary predictions**:

- **A-H1 (Phase transition)**: Crystallization rate (proportion of seeds crystallized)
  is non-monotonic in δ — near-zero at very low δ (insufficient deposition to form
  trails), rises through an intermediate peak, then declines at very high δ (near-uniform
  pheromone field; no directional gradient). The sharpness of this transition constitutes
  the "phase-like regime shift" predicted by Δ-Variable Theory for implicit systems.
- **A-H2 (SCI peak)**: SCI peaks at the same intermediate δ range as crystallization rate.
  At low δ: Δ-events rarely close within τ (no reinforcement). At high δ: Δ-events are
  rare (near-universal gradient following) so SCI is ill-defined; on valid events, closure
  is fast. The non-monotonic SCI-by-rate pattern matches Exp 14 (coupling window) analogue.
- **A-H3 (Throughput)**: Throughput increases with δ up to the optimal range, then
  plateaus or slightly declines (diminishing gradient signal at saturation).

**Falsification criterion for A-H1**: If crystallization rate increases monotonically
with δ (no decline at high δ), the phase-transition prediction fails. This would mean
the system lacks the sharp regime boundary predicted by the theory.

### Experiment C — Coupling-Window Characterization

**Purpose**: Characterize SCI as a function of τ to validate the τ=20 preregistration
and document the reinforcement timescale of the stigmergic system.

**Fixed**: δ=0.10, ε=0.01, θ_decision=0.1213, grid=50×50, n_ants=100, n_steps=2000.

**Variable**: τ ∈ {5, 10, 20, 40, 80} (5 levels).

**Seeds**: 30 per condition (seeds 0–29).

**Total runs**: 5 × 30 = 150 runs (can reuse the δ=0.10 Exp A runs for τ=20 condition).

**Outcome variables** (per run): SCI(τ) for each τ level.

**Primary predictions**:

- **C-H1 (Monotone increase)**: SCI(τ) increases monotonically with τ — larger window
  always yields higher closure probability (more time for reinforcement). This is a
  necessary condition for τ being a meaningful measurement parameter.
- **C-H2 (τ=20 mid-range)**: SCI(20) falls in the 50–90% range, confirming the
  preregistered τ is neither trivially short (most events unclosed) nor so long that
  SCI ≈ 1.0 (all events trivially close). A τ where SCI is near 0 or 1 has poor
  discriminative power.
- **C-H3 (Characteristic timescale)**: The SCI curve shows a characteristic "knee"
  — rapid increase from τ=5 to τ=20, then slower increase from τ=20 to τ=80 — marking
  the typical reinforcement latency of the stigmergic system.

**This experiment does not alter the preregistered τ=20.** It characterizes the system
and validates the choice post-hoc.

---

## Module 2 — Bridge Formation (Experiment B)

### Environment

| Parameter | Value | Notes |
|---|---|---|
| corridor_length | 50 | Grid columns |
| corridor_width | 3 | Grid rows |
| Nest | col = 0 | Left side |
| Food | col = 49 | Right side |
| n_ants | 100 | Initially all WALKING |

### State Machine

Three states: WALKING (0), LOCKED (1), LEAVING (2).

**WALKING → LOCKED (Join rule)**:
An ant at a bridge-eligible position (col ∈ [gap_start−1, gap_end+1]) that:
(a) failed to move this step (blocked by impassable gap), **and**
(b) has transit count ≥ join_threshold in the last traffic_window steps
→ transitions to LOCKED at current position.

*"Transit count"*: number of WALKING ants entering the focal ant's cell during the
traffic window. Implemented as a per-ant rolling sum over a circular buffer.

**LOCKED → LEAVING (Leave rule)**:
A LOCKED ant that receives **zero traffic** (transit_sum = 0) for leave_patience
consecutive steps → transitions to LEAVING.

Traffic = number of WALKING ants that arrived at the locked ant's cell in the last
traffic_window steps (rolling sum). A locked ant receiving zero traffic is idle —
the bridge is not being used at that position (slackness proxy).

*Implementation note*: The original population-count leave rule (Moore neighborhood
locked count vs. n_equilibrium) was rejected because n_equilibrium scales as
round(0.51 × gap_size) and exceeds the maximum Moore neighborhood size (8) for gaps
≥ 17 cells, causing immediate dissolution at large gaps. The global bridge-size
comparison (total locked vs. n_equilibrium) was also tried but produces a "ratchet"
(bridge grows to fill all cells, never dissolves). The traffic-based leave rule is
the correct biological proxy: a locked ant stays as long as ants walk over it.

**LEAVING → WALKING**: immediate on next step.

### Gap Traversability

Gap cells (col ∈ [gap_start, gap_end]) are impassable to WALKING ants unless:
- A LOCKED ant is already at that cell, **or**
- A LOCKED ant is at the adjacent cell in the direction of travel.
  (outbound: col−1; return: col+1)

Bridges grow incrementally as LOCKED ants occupy adjacent gap cells from the edges
inward. A full bridge spans the complete gap_start..gap_end range.

### Locked Parameters (Derived from Literature)

| Parameter | Value | Source |
|---|---|---|
| reid_coefficient | 0.51 | Reid et al. (2015): 0.51 ants/mm |
| n_equilibrium | round(0.51 × gap_size) | Formation criterion only |
| min_jump_size | 3 | Gaps ≤ 3 units directly traversable |
| join_threshold | 1 | Any transit triggers lock |
| traffic_window | 5 steps | Rolling transit count window |
| leave_patience | 5 steps | Consecutive zero-traffic steps to leave |
| gap_min | 1 | Ramp start |
| gap_max | 30 | Ramp end |
| hold_steps | 500 | Steps per gap_size level |
| n_ants | 100 | Colony size |

**min_jump_size rationale**: Army ants (Eciton spp., ~3–5 mm body length) can step
across gaps of ≤ 1–2 body lengths without a bridge. At 1 grid unit ≈ 1 mm, gaps of
3 units or fewer are directly walkable. Gaps of 4+ units require a bridge. This is
the physical basis for the formation threshold and is the mechanism by which
dissolution_gap < formation_gap (hysteresis) arises.

### Ramp Protocol

1. **Warmup** (500 steps at gap_size = gap_min): allow colony to establish initial
   bridge behavior before ramp begins. Warmup data not used in analysis.
2. **Ramp up**: increase gap_size by 1 unit every hold_steps steps, from gap_min to
   gap_max. At each gap_size level, record mean bridge size (LOCKED count) during
   hold period.
3. **Ramp down**: decrease gap_size by 1 unit every hold_steps steps, from gap_max
   back to gap_min. At each gap_size level, record mean bridge size during hold period.

### Outcome Variables

Per seed:

1. **bridge_size_up[g]**: mean LOCKED count at gap_size = g during ramp-up.
2. **bridge_size_down[g]**: mean LOCKED count at gap_size = g during ramp-down.
3. **formation_gap**: smallest g (during ramp-up) where mean bridge_size ≥ n_equilibrium(g).
4. **dissolution_gap**: smallest g (during ramp-down) where mean bridge_size = 0
   (bridge fully dissolved).
5. **hysteresis_detected**: bool — dissolution_gap < formation_gap.
6. **hysteresis_magnitude**: formation_gap − dissolution_gap (positive = hysteresis confirmed).
7. **throughput**: round trips per step (mean over ramp period).

### Experiment B — Gap-Size Hysteresis

**Purpose**: Test whether bridge formation exhibits hysteresis — formation threshold ≠
dissolution threshold — as predicted by the asymmetric join/leave rules and confirmed
empirically by McCreery et al. (2022).

**Fixed**: all BridgeConfig parameters as above.

**Seeds**: 30 (seeds 0–29).

**Total runs**: 30 runs.

**Primary predictions**:

- **B-H1 (Hysteresis present)**: dissolution_gap < formation_gap in ≥ 20/30 seeds
  (66.7%). The leave rule requires *sustained* low neighbor count (leave_patience steps),
  while the join rule requires only a *single* transit event within traffic_window. This
  asymmetry produces different up/down thresholds even in a model with no learning.
- **B-H2 (Path-dependence effect size)**: mean(bridge_size_down[g] / bridge_size_up[g])
  > 1.3 for gap sizes g ∈ [formation_gap, 2×formation_gap], across seeds. This measures
  the MAGNITUDE of path-dependence: the bridge is substantially larger during
  dissolution than during formation at the same gap size. Expected ratio ≈ 1.5x based
  on pilot (seed 0: mean ratio = 1.62 for g ∈ {4..13}).
- **B-H3 (Magnitude)**: mean hysteresis_magnitude ≥ 1 gap unit across hysteretic seeds.
  The 1-unit threshold reflects the discrete-grid minimum: dissolution_gap = min_jump_size
  and formation_gap = min_jump_size + 1 by model construction. This is expected to be
  constant across seeds (deterministic), confirming the structural asymmetry.

**Note on B-H3**: Hysteresis magnitude = 1 is mechanistically determined (the bridge
forms at gap = min_jump_size + 1, dissolves at gap = min_jump_size). The magnitude in
gap units is modest but real. The larger effect is captured in B-H2 (bridge size ratio
≈ 1.5–1.8× at same gap values). B-H2 is the primary path-dependence test; B-H3
confirms the directional asymmetry at the mechanistic level.

**Falsification criterion for B-H1**: If hysteresis is present in < 15/30 seeds
(50%), the structural-residue prediction for implicit Δ fails in the bridge domain.

### Seeds and Replication

30 seeds per experiment (seeds 0–29). This matches the n=30 target in the extended
experiment menu and is sufficient for single-sample Wilcoxon and proportion tests
with medium effect sizes.

---

## Statistical Analysis Plan

### Module 1 (Experiments A and C)

**Exp A — Phase transition test (A-H1)**:
- Compute crystallization_rate per δ level (proportion of 30 seeds crystallized).
- Test for non-monotonicity: Jonckheere-Terpstra trend test with expected direction
  reversal at high δ; or fit a quadratic to rate-vs-δ and test the quadratic term.
- Planned comparison: crystallization_rate at δ=0.10 (preregistered optimal) vs.
  δ=0.04 (low) and δ=0.30 (high). Direction: rate(0.10) > rate(0.04) and rate(0.10)
  ≥ rate(0.30). Two-sample binomial tests, one-tailed, Bonferroni-corrected (α=0.025).

**Exp A — SCI test (A-H2)**:
- Compute mean SCI per δ level.
- Pearson correlation of SCI vs. δ. Sign alone is not the test (A-H2 predicts
  non-monotonic). Report SCI at each δ level; confirm SCI peaks at same level as
  crystallization rate.

**Exp C — τ characterization**:
- Report mean SCI(τ) across 30 seeds for each τ level.
- Confirm C-H1 (monotone): one-sided paired test SCI(τ_high) > SCI(τ_low) for
  adjacent τ levels (5 paired tests, Bonferroni α=0.01).
- Report SCI at τ=20 with 95% CI. Confirm C-H2: SCI(20) ∈ (0.50, 0.90).

### Module 2 (Experiment B)

**B-H1 (Hysteresis proportion)**:
- Proportion test: H0: P(hysteresis_detected) ≤ 0.50. One-sided binomial test.
  Success threshold: ≥ 20/30 seeds with dissolution_gap < formation_gap (p < 0.05).

**B-H2 (Direction, path-dependence)**:
- For each gap size g and each seed: binary indicator bridge_size_down[g] ≥ bridge_size_up[g].
- Across all (seed, g) pairs: proportion of pairs showing the predicted direction.
  One-sided binomial test vs. H0: P = 0.50.

**B-H3 (Magnitude)**:
- One-sample t-test: mean hysteresis_magnitude (in hysteretic seeds only) vs. null=2.
  One-sided H1: mean > 2. α = 0.05.

### Overall Significance

Each module's predictions are evaluated independently. Bonferroni correction is applied
within each experiment's hypothesis family (not across modules). The ant modules are
a *separate* preregistered test from P1–P5 (which test explicit Δ in MARL). Results
are reported in their own section (Supplementary: Implicit Δ experiments).

---

## Implementation Reference

| Item | Location |
|---|---|
| Module 1 simulation | `backend/simulation/ants/colony.py` |
| Module 2 simulation | `backend/simulation/ants/bridge.py` |
| Module 1 smoke test | `backend/run_ant_smoke.py` |
| Module 2 smoke test | `backend/run_bridge_smoke.py` |
| Module 1 campaign runner | `backend/run_ant_campaign.py` (to be built) |
| Module 2 campaign runner | `backend/run_bridge_campaign.py` (to be built) |
| Output directory | `data/ant_experiments/` |

### Smoke Test Results (Verified Before Lock)

**Module 1** (`python run_ant_smoke.py`, delta=0.10, epsilon=0.01, seed=0):
```
Pilot calibration: 1966/2500 cells non-zero
  p25=0.1213  p50=0.3285  p75=0.7651  max=2.7011
=> theta_decision (25th pct) = 0.1213

Entropy: step 0: H=1.563 (13.9%)  step 1000: H=10.804 (95.7%)  step 2000: H=7.219 (64.0%)
No crystallization in 2000 steps (threshold: 6.77 bits; trail forming but not fully crystallized)
Crystallization confirmed at delta=0.20: step 1921
SCI: 0.0036 (128486 Delta-events, 458 resolved)
Throughput: 0.2595 food/step (519 delivered)
```

**Module 2** (`python run_bridge_smoke.py`, gap=10, steps=1000, seed=0):
```
gap_size=10  corridor=3x50  n_ants=100  n_equilibrium=5  min_jump_size=3
step     1: LOCKED=  3  WALKING= 97  LEAVING=0  throughput=0.0000
step  1000: LOCKED= 27  WALKING= 73  LEAVING=0  throughput=0.6970
Final bridge size: 27 (n_equilibrium=5)  PASS: bridge formed and stabilized
gap_size=0: Max LOCKED=0  PASS: no locking with gap_size=0  Throughput=1.000000

3-seed ramp pilot (seeds 0-2, gap 1-30):
  formation_gap=4, dissolution_gap=3, hys_mag=1  (all 3 seeds identical)
  bridge_size_down/bridge_size_up ratio (g=4..13): mean ~1.60 (range 1.5-1.8)
```

Both smoke tests pass. Parameters confirmed as implemented.

---

## Preregistration Lock

All parameters in this document are fixed as of **2026-03-01**.

Campaign runs must not begin before this document is committed to the repository.
Any deviation from these parameters must be reported as exploratory in publications.
Parameter changes that increase confirmatory power are prohibited post-lock.

The θ_decision and τ values above were determined by pilot calibration (seeds 0,
delta=0.10, epsilon=0.01) and may not be re-calibrated on campaign seeds.
