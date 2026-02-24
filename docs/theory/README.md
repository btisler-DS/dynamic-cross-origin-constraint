# Theory

Working documents supporting the Δ-Variable Theory of Interrogative Emergence.

---

## Documents in This Folder

| File | Description |
|------|-------------|
| [`counter-wave-discrimination.md`](counter-wave-discrimination.md) | Three competing hypotheses for the full-survival DECLARE spikes observed in Run 11, with six discriminating experiments |
| [`menu of concrete experiments.docx`](menu%20of%20concrete%20experiments.docx) | Post-confirmatory experimental roadmap — 17 experiments across 6 categories |

These documents are **post-pilot-data** working notes. They are not part of the
locked preregistration. Per the OSF commitment, they will be reported as exploratory
analysis, not confirmatory results. See [`../preregistration.md`](../preregistration.md).

---

## Core Claim

Interrogative states are not linguistic phenomena. They are **Δ-variables** — explicitly
represented, unresolved dependency variables that require external information for resolution
and create mandatory coupling between coordinating systems.

This is a structural claim, not a behavioural one. The experiment tests whether the structure
emerges spontaneously under the right conditions, not whether agents can be trained to ask
questions.

---

## Five Propositions

1. **Structural Necessity** — Interrogative states emerge as optimal solutions to uncertainty
   management, not as linguistic phenomena
2. **Cost-Benefit Optimization** — Systems develop interrogative behaviour despite higher energy
   costs when coordination benefits exceed expenditure
3. **Forced Coupling** — Unresolved Δ-variables create dependency edges requiring inter-system
   coordination
4. **Silent Collapse Prevention** — Systems that act without resolving acknowledged uncertainty
   exhibit coordination failure
5. **Substrate Independence** — Under identical constraints, different cognitive architectures
   converge on similar Δ-management strategies

---

## Theoretical Grounding

### AnnA — Adaptive, non-neural Axiom
*Puchtel (2026)*

Formal axiomatic framework for intelligence as coherence under pressure. Provides the
deductive basis for why Δ-variables must emerge: coherence under pressure requires resolving
unresolved dependencies before acting; a Δ-variable is precisely an explicitly represented
unresolved dependency. The experiment confirms what the axioms predict.

Key definitions:
- **Intelligence** = maintenance of coherence under pressure over time
- **Structure** = constraint-bearing residue of interaction
- **Regulation** = redistribution of pressure under constraint

Adopted phrasings for this project:
- *"Constraint-bearing residue"* — what crystallisation is
- *"Regulation without command"* — Agent C's broker function
- *"Pressure redistribution"* — the D/Q/R type dynamics

### Intelligence Beyond Neurons
*Puchtel (2026), Chapters 1–6*

Chapter-by-chapter argument that intelligence is not grounded in signals, representation,
models, optimization, control, or prediction. Used in the paper's Related Work section to
motivate a constraint-grounded account:

- Ch. 1 — Signal-based accounts cannot explain why signal *type* matters
- Ch. 2 — Representation-based accounts cannot explain emergence from energy constraints alone
- Ch. 4 — Optimization-based accounts cannot explain limit-cycle behaviour (non-convergence)
- Ch. 5 — Agent C's GNN broker role as regulation without command
- Ch. 6 — Prediction emerging within stabilised D/Q/R balances (post-crystallisation QRC lock-in)

The final pages contain an explicit mapping table from each chapter to Cross-Origin-Constraint
simulation behaviours.

---

## Open Question: Counter-Wave Phenomenon

Run 11 (pilot data) shows full-survival events at E202, E381, E390 causing DECLARE spikes
and entropy rebounds. Three competing explanations are under investigation:

**H1 — Reward artifact**: DECLARE exploits the terminal survival bonus; spike vanishes if
bonus is removed or smoothed.

**H2 — Phase reset**: Episode boundary triggers a learned mode transition; spike persists
without terminal reward as long as the boundary event exists.

**H3 — Pragmatic content**: DECLARE on success is a genuine coordination speech act —
"goal achieved, stop querying." Entropy rebound is pressure relaxation, not noise. Rebound
should be suppressed if pressure is maintained after success.

The most decisive single test: *reward without boundary* — give the success reward but
continue the episode. If the spike follows the reward, H1. If it follows the termination
event, H2. If the rebound depends on whether pressure continues, H3.

See [`counter-wave-discrimination.md`](counter-wave-discrimination.md) for the full
experiment design. These hypotheses were generated after observing pilot data and will
be reported as exploratory analysis.

---

## Literature Gap

Elicit systematic review (2026) screened 50 papers on mathematical foundations of language
emergence. Of 10 included studies, none make the ontological identity claim that language
operations *are* mathematical at the substrate level. All use mathematics as an analytical
tool. This is the gap the Δ-Variable experiment addresses directly.

---

## Paper Structure

1. **Introduction** — The gap (Elicit review); frameworks that approach it (AnnA/IBN);
   the missing empirical piece
2. **Theoretical Framework** — AnnA axioms → Δ-variable definition follows deductively;
   why existing frameworks are insufficient (IBN prohibition arguments)
3. **Experiment** — Preregistered design; five cost conditions; 15 seeds; 500 epochs
4. **Pilot Data** — Run 11 exploratory results (three crystallisation waves, counter-waves,
   QRC persistence from E280); excluded from confirmatory testing
5. **Results** — Confirmatory experiment (P1–P5)
6. **Discussion** — Substrate independence; counter-wave hypotheses; limit-cycle behaviour;
   implications for the ontological status of interrogative structure
