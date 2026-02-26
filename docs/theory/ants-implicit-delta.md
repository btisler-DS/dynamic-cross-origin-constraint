# Implicit vs. Explicit Δ: The Ant Case

*Working document — drafted 2026-02-25.*
*Source: dialogue in temp_talk.txt. Target: Discussion Section 6.3 of the paper.*

---

## The Core Question

Δ-Variable Theory (Proposition 1) currently states:

> Interrogative states are Δ-variables — explicitly represented unresolved dependency variables
> requiring external information for resolution.

Ants resolve dependencies under constraint without explicit representation, without symbolic
tokens, without discrete QUERY/RESPOND acts. This appears to challenge Proposition 1.

It doesn't. It sharpens it.

---

## The Invariant

Stripping away implementation layers, the structural kernel of Δ is:

> **Capacity-bound dependency under partial observability that cannot be resolved locally.**

Symbolic interrogatives (QUERY tokens in MARL) are one implementation of this kernel.
Stigmergic reinforcement (pheromone gradient dynamics in ant colonies) is another.

Neither the representation nor the token is load-bearing. The constraint is.

---

## Implicit vs. Explicit Δ — Formal Distinction

**Explicit Δ** (MARL agents, humans, language):
- Unresolved dependency is *internally represented*
- Dependency is *externally declared* via symbolic act (QUERY token)
- Closure is *acknowledged*: RESPOND token confirms resolution
- Failure mode: agent acts despite unresolved acknowledged dependency
  → Silent Collapse (Proposition 4)

**Implicit Δ** (ant colonies, stigmergic systems):
- Unresolved dependency manifests as *deficit in local gradient information*
- No internal representation; no external declaration
- Dependency *experienced as constraint pressure* — junction with insufficient
  pheromone gradient to select a path
- Closure: returning forager reinforces gradient within τ steps, enabling directional
  choice — functionally equivalent to RESPONSE closing a QUERY
- Failure mode: persistent low-gradient stagnation; no reinforcement cycle; colony failure
  → Implicit analogue of QRC → 0

Both systems have a collapse mode. They manifest differently because acknowledgment is
not available in implicit systems — but the structural consequence (failure to resolve
dependency → coordination breakdown) is identical.

---

## Stigmergic Coupling Index (SCI)

QRC cannot be applied directly to ant systems (no QUERY tokens to detect). The analogous
measure:

> **Stigmergic Coupling Index (SCI)**
> Fraction of local stalls (junctions with pheromone gradient below decision threshold)
> resolved via neighbor-mediated gradient reinforcement within τ steps.

Formal definition:
- **Δ-event**: ant reaches junction where pheromone gradient < θ_decision (insufficient
  information to select path direction)
- **Closure**: gradient reinforced by returning forager(s) within τ steps, crossing θ_decision

SCI = P(closure within τ | Δ-event at t)

This is QRC stripped of symbolic tokens. If SCI behaves under cost sweep the same way QRC
does — non-monotonic peak at intermediate deposition cost, hysteresis under evaporation
reversal, phase-like regime shift — then the functional relationship (dependency → forced
coupling → closure) persists without representation.

---

## Existing Empirical Evidence

### Reid et al. (2015, PNAS) — Army Ant Bridge Hysteresis

Army ant bridges (Eciton burchellii) persist after traffic density drops below the threshold
required to form them. Formation threshold ≠ dissolution threshold. The bridge exists as
structural residue in the colony's behavioral state.

This is precisely the signature Experiment 2 (hysteresis under frozen-policy reversal) seeks
in the MARL system:
- Different "up" and "down" thresholds → path dependence
- Persistence below formation threshold → structural residue, not reward equilibrium

Reid et al. provides this signature in a system with:
- No internal modeling
- No symbolic signaling
- No token protocol
- No representational memory

It is embodied hysteresis. The structural-residue prediction holds in a substrate that cannot,
by any account, be using representation to sustain it.

---

## Mapping Ants to the 17-Experiment Battery

| Experiment | MARL intervention | Ant analogue | Prediction |
|---|---|---|---|
| 1 (Tax sweep) | Sweep query cost | Sweep pheromone deposition cost | Sharp colony shift from wandering → stable path in narrow band |
| 2 (Hysteresis) | Frozen-policy tax reversal | Raise evaporation rate, then lower it; no learning | Trail persists below formation threshold (Reid et al. already shows this) |
| 6 (Broker audit) | Ablate Agent C | Remove privileged super-sensing ant type | Colony degrades but survives → distributed; collapses entirely → centralized |
| 11 (Saturation) | Force energy depletion | Overload colony (high metabolic cost, forced bridge use) | Visible coordination failure at capacity exceedance |
| 12 (Irreversibility) | Overload then restore | Restore cost after overload | Permanent drift in path efficiency → history-bearing structure |
| 14 (Coupling window) | Sweep query/respond cost | Sweep deposition cost | Non-monotonic SCI peak at intermediate cost |

---

## Proposed Revision to Proposition 1

**Current:**
> Interrogative states are Δ-variables — explicitly represented unresolved dependency variables
> requiring external information for resolution and creating mandatory coupling between
> coordinating systems.

**Revised (minimal, surgical):**
> Interrogative states are explicitly represented Δ-variables in systems with sufficient
> representational capacity. In systems lacking such capacity, Δ manifests implicitly as
> deficit in local gradient information, resolved through environment-mediated coupling with
> functionally equivalent structural signatures.

No collapse. No retreat. The five propositions otherwise stand unchanged.

---

## Revised Proposition 5 Extension

**Current Proposition 5:**
> Under identical constraints, different cognitive architectures converge on similar
> Δ-management strategies.

**Add two sentences:**
> This convergence extends to systems without representational capacity. Ant colonies under
> metabolic cost and partial observability exhibit phase-like coordination formation,
> structural residue (hysteresis), and coupling-window effects — the same structural
> signatures predicted by Δ-Variable Theory — through stigmergic gradient dynamics rather
> than symbolic interrogative acts.

---

## Falsification Boundary

The ant case is not merely illustrative — it is a genuine falsification test for Proposition 5.

If ants showed:
- No hysteresis (smooth monotonic trail formation/dissolution)
- No intermediate coupling window (SCI declines monotonically with deposition cost)
- No phase-like regime shift (gradual wandering → path formation)

Then implicit Δ would fail while explicit Δ holds. Substrate independence would fracture.
The theory would be restricted to representational systems only.

The Reid et al. hysteresis result falsifies that outcome for the bridge case. Experiments 1
and 14 analogues remain to be run for the foraging case.

---

## Draft: Discussion Section 6.3

**Implicit vs. Explicit Δ: Substrate Extremes**

The current experimental scope is restricted to explicitly representational systems —
heterogeneous neural agents with sufficient capacity for symbolic signaling, discrete type
tokens, and codebook formation. This is an acknowledged scope boundary, not a theoretical
limitation.

However, existing empirical evidence from non-representational systems suggests the
structural signature of Δ is not unique to symbolic agents. Reid et al. (2015) demonstrated
that army ant (Eciton burchellii) bridges persist below the traffic density threshold that
triggers their formation — a clear hysteresis signature in a system with no internal
modeling, no symbolic signaling, and no representational memory. This is precisely the
structural residue Experiment 2 tests under frozen-policy tax reversal in the MARL system.
If the residue signature appears in a substrate that cannot, by any account, be sustaining it
through representation, the invariant cannot be the representation. It must be the constraint.

This motivates a formal distinction between explicit and implicit Δ. Explicit Δ — as
operationalized in this study — is an unresolved dependency that is internally represented
and externally declared via symbolic act. Implicit Δ is the same structural kernel —
capacity-bound dependency under partial observability that cannot be resolved locally —
manifesting as a deficit in local gradient information, resolved through environment-mediated
coupling. Ant foraging provides the clearest case: an ant at a junction with insufficient
pheromone gradient faces an implicit Δ-event; closure occurs when returning foragers
reinforce the gradient within τ steps, enabling directional choice. The functional
relationship (unresolved dependency → forced coupling → closure) holds without a single
symbolic token.

Silent collapse (Proposition 4) maps cleanly to this framework. In explicit systems, the
failure mode is an agent that acts despite an acknowledged unresolved dependency. In implicit
systems, acknowledgment is not available; the analogue is persistent low-gradient stagnation
— no reinforcement cycle, coordination breakdown, colony failure. Both are instances of the
same structural failure: Δ unresolved at the time of action.

Proposition 1 therefore requires a scope qualifier rather than a revision: interrogative
states are explicitly represented Δ-variables in systems with sufficient representational
capacity; in systems lacking such capacity, Δ manifests implicitly with functionally
equivalent structural signatures. Proposition 5 (Substrate Independence) is strengthened
rather than threatened: the structural signatures predicted by Δ-Variable Theory — phase-like
regime formation, hysteresis, non-monotonic coupling window — appear across the full
representational spectrum, from symbolic MARL agents to stigmergic insect colonies. Testing
this convergence explicitly across substrates is the scope of Protocol 3 and beyond the
current study.
