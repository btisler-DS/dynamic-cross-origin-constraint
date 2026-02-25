# Foundational Questions — Answered

*Drafted 2026-02-25. Intended audience: paper Theory, Methods, and Discussion sections.*
*Source questions: "menu of concrete experiments extended.docx" — sections 1.1 through 10.3.*

---

## 1. Foundational Framing

### 1.1 What exactly is the null model?

The null model is: **standard multi-agent reinforcement learning with communication cost, where all
observed coordination is attributable to reward gradient alignment.** Formally, under the null,
an agent communicates when and only when the expected marginal reward from communication exceeds
its marginal cost. All observed structure — type entropy reduction, QRC elevation, protocol
emergence — is predicted to be a monotonic function of the cost-benefit ratio. No phase
transitions, no path dependence, no structural residue. Just smooth performance scaling.

The structural account predicts that the null fails in a specific way: the transition from noise
to protocol is discontinuous, path-dependent, and leaves residue that persists after the
incentive that created it has been removed. The experiments are designed to distinguish these
two outcomes, not merely to show that communication helps performance.

### 1.2 What is being held constant?

Across all 17 experiments, the following are held constant: network architecture (Agent A = GRU,
Agent B = CNN, Agent C = GNN), hidden dimension (128), optimizer (Adam, lr = 3e-4), agent
count (3), episode length (50 steps), episodes per epoch (10), environment geometry (10x10
grid, 3 targets), and reward structure except for the specific intervention variable. Seeds are
varied (N=15 per condition) to characterize distributional outcomes rather than point estimates.
Only the intervention variable changes per experiment. Where multiple cost parameters are
modified simultaneously (e.g., declare_cost and query_cost in the same run), this is the
intervention, not uncontrolled covariation.

### 1.3 Are these agents optimizing a global reward?

No. Each agent optimizes its own individual REINFORCE objective with no shared value function
and no centralized training signal. Agent i receives: `env_reward_i - (cost_multiplier *
signal_magnitude) + survival_bonus * energy_fraction`. There is no global objective.

The coordination that emerges is not programmed and not the result of a joint optimization
target. It arises because agents cannot reach targets without resolving spatial dependencies
that require information held by other agents. The coupling is environmental, not architectural.
This is the structural claim: the coordination protocol is a necessary consequence of the
dependency structure of the task, not a designed feature of the training objective.

---

## 2. Measurement

### 2.1 Why QRC?

QRC (Query-Response Coupling) is theoretically privileged because it directly operationalizes
the Delta-variable closure condition. A Delta-variable is an unresolved environmental dependency
requiring external information to resolve. QRC measures whether that resolution occurs: given
that agent i emitted a QUERY at time t, did agent j emit a RESPONSE within 3 timesteps?
QRC = 1.0 means every interrogative state achieves closure.

No other single metric captures this. Type entropy (H) measures distributional structure but
not temporal coupling. Mutual information between agent signals measures statistical dependence
but not directed closure. Survival rate measures outcome but not mechanism. QRC is the only
metric that tracks the causal chain from dependency declaration to resolution — which is exactly
what the theory predicts should be load-bearing.

### 2.2 Entropy of what distribution?

H is the Shannon entropy of the per-epoch signal type distribution:

    H = -sum[ p(type) * log2(p(type)) ]   for type in {DECLARE, QUERY, RESPOND}

where p(type) is the proportion of signals of that type emitted across all agents and all
timesteps in a given epoch. Maximum H = log2(3) ≈ 1.585 bits (uniform distribution).

This is **message type entropy** — not token entropy, not conditional entropy, not temporal
entropy. It measures diversity of communicative intent across the epoch. It does not measure
the information content of individual signals.

### 2.3 How do you distinguish compression from impoverishment?

Low H is ambiguous in isolation. It can indicate either:
- **Structured protocol**: agents have specialized; most signals are RESPOND because QUERYs
  are being answered efficiently
- **Degenerate collapse**: all agents emit only DECLARE; the query-response cycle never forms

The diagnostic is the **joint (H, QRC) signature**:
- Structured protocol: low H, high QRC — entropy fell because the cycle stabilized
- Degenerate collapse: low H, low QRC — entropy fell because one type dominates without closure

The counter-wave phenomenon in Run 11 provides direct evidence that the system operates in the
structured protocol regime: full-survival events cause H to rebound (DECLARE spikes briefly,
then reverts) while QRC remains elevated. If the system were degenerate, survival success would
not trigger a temporary DECLARE surge followed by reversion to RESPOND dominance.

### 2.4 What defines "crystallization"?

Crystallization is operationally defined as: **the first epoch at which type entropy H < 0.95
for five consecutive epochs.** The threshold 0.95 is approximately 60% of maximum entropy —
a qualitative shift from near-uniform type distribution toward a dominant protocol signature.
The 5-epoch window filters transient dips.

This definition is implemented in `simulation/engine.py:_find_crystallization_epoch()` and
recorded in each run's `manifest.json`. It is a threshold rule, not a formal statistical test.
This is appropriate for a discovery paper. In follow-up work, crystallization should be
identified via order parameter variance measurement near the critical band — the variance of H
across seeds should peak at the phase boundary before collapsing as the protocol locks in.

---

## 3. Phase Transition Claims

### 3.1 How are you testing for actual phase behavior?

The campaign (5 conditions x 15 seeds x 500 epochs) tests for phase transition signatures via
the distribution of outcomes across seeds per cost condition. Predicted signatures:
- **Sharp transition**: seeds cluster tightly around a crystallization epoch within each
  condition; the distribution of crystallization epochs is bimodal across the cost range
  (frequent crystallization above threshold, rare below)
- **Smooth scaling**: crystallization epoch shifts gradually and monotonically; no bimodality

This does not formally confirm critical exponents or finite-size scaling. Those require sweeping
agent population size — planned for Protocol 2 but not in the current study. The current
evidence is consistent with a phase transition but should be described as "phase-transition-like
behavior" in the paper rather than claiming exact universality class membership.

### 3.2 Could hysteresis arise from learning inertia?

Yes — this is the most important confound and must be controlled for by design. If gradient-
based training is active during the reversal phase, hysteresis could reflect optimizer momentum
(large weight updates inertia) rather than structural residue in the learned representation.

**Required control**: the reversal phase of the hysteresis experiment must be run with **frozen
policy weights**. Agents evaluate (no gradient updates) while tax decreases. Under frozen
weights, any persistence of the crystallized protocol reflects structural residue in the weight
landscape itself — not optimization lag. This is a hard implementation requirement for
Experiment 2, not an optional refinement.

---

## 4. Locality and Non-Substitutability

### 4.1 Is locality enforced architecturally or emergent?

In the current harness, locality is partially enforced at the observation level (agents see a
local window of the grid) but communication is global (any agent can signal to any other via
CommBuffer). The environment does not enforce spatial communication constraints.

This makes the locality experiments a stronger test, not a weaker one. The question becomes:
does emergent locality appear despite architectural broadcast capability? If coherence breaks
down when a local agent is removed — even though the remaining agents could in principle
compensate via global broadcast — then the locality constraint is emergent from the dependency
structure of the task, not imposed by the architecture.

### 4.2 How do you detect hidden centralization?

The broker privilege audit (Experiment 6) tests this via TE centrality and ablation impact.
If Agent C's removal causes complete coherence collapse (QRC → 0, H → maximum), centralization
is present. If removal causes graceful degradation (protocol degrades but survives at reduced
QRC), structure is distributed.

The theoretical expectation: because each agent's Delta-variables require different information
(Agent A requires path history, Agent B requires spatial pattern, Agent C requires relational
context across agents), no single agent can be the sole closure mechanism. The Forced Coupling
proposition predicts distributed protocol, not hub formation. If Agent C becomes a hub, this
is a falsifying result for the distributed coherence claim — not a confirmation of it.

---

## 5. Capacity and Irreversibility

### 5.1 What constitutes "capacity"?

In this harness, capacity is the agent's **energy budget** — a finite resource that depletes
with each signal emitted and each action taken, restored at a fixed rate each epoch. An agent
that exhausts its energy budget cannot signal or act; survival requires maintaining energy
above zero. This is a concrete, measurable implementation of the capacity concept in
constraint-bearing systems.

Other capacity dimensions (memory bandwidth, computation limits) are architectural constants
in this study and are swept only in Experiments 8 and 9. Energy budget is the primary capacity
lever because it directly modulates the cost of Delta-variable resolution.

### 5.2 What prevents full reset?

The irreversibility test must be run on the **final checkpoint of a crystallized run**, not by
retraining from scratch. Protocol:
1. Run to crystallization (standard 500-epoch run)
2. Apply overload phase (increase energy drain rate beyond recovery threshold for N epochs)
3. Restore energy parameters to pre-overload values; resume training on the same checkpoint

If the post-overload system shows permanent drift in crystallization epoch distribution,
increased fragility under subsequent overload, or reduced QRC ceiling — the damage is encoded
in the weight landscape and resource restoration does not erase it.

Full reset would require re-initializing weights to pre-crystallization values. That is a
different experiment (and would confirm that the structure is in the weights, not in the
environment), and should be run as a control condition alongside the irreversibility test.

---

## 6. Representation

### 6.1 How do you know representation isn't implicitly formed?

The honest answer: you cannot fully rule out implicit representation in recurrent agents.
Agent A's GRU hidden state may encode a partial world model. This is an acknowledged scope
boundary.

The claim is not "these agents have no internal representations." The claim is "the coordination
protocol is structurally necessary given the agents' capacity constraints and the environmental
coupling requirements." Whether the mechanism involves implicit representation is a separate
question from whether the coordination is structurally driven. An implicit world model in the
GRU state does not make the Delta-variable closure any less real — it is the mechanism by which
the agent resolves its Delta-variables, not an alternative explanation for why the protocol
emerges.

The memory depth scaling experiment (Experiment 8) provides indirect evidence: if a sharp
memory threshold exists below which protocol fails to emerge under extended training, the
threshold indicates a structural depth requirement — regardless of whether the representation
is explicit or implicit.

### 6.2 Memory depth knee — artifact or necessity?

The confound: a memory threshold could reflect **optimization difficulty** (shallow agents fail
to learn the policy given training time) rather than a structural constraint (shallow agents
cannot sustain the protocol even at convergence).

Required control: compare shallow agents trained to convergence vs. shallow agents given 3x
the training budget. If the knee is an optimization artifact, additional training closes the
gap. If it persists under extended training, the threshold reflects a structural constraint
that cannot be trained around. This is a required control for Experiment 8 and must be
preregistered before running.

---

## 7. Generalization and Compositionality

### 7.1 What counts as compositional novelty?

Primitives are defined operationally as coordination patterns for distinct environmental
configurations: for example, single-target navigation with one agent occluded (primitive A)
and multi-target relay requiring cross-agent handoff (primitive B). These are trained
separately. Novelty is tested by presenting A+B conditions simultaneously — a configuration
never seen during training on either primitive alone.

Successful generalization: agents achieve target acquisition rates comparable to jointly
trained baselines using signal type distributions consistent with their established protocols
(not tabula rasa re-learning).

Overlap between primitives' latent structure is measurable via centroid distance in PCA signal
space across the two conditions. If the PCA centroids for primitive A and primitive B are not
well-separated, the primitives were not genuinely independent and the novelty test is invalid.
Primitive separation must be confirmed before the generalization test is run.

---

## 8. Coupling Window

### 8.1 Why should intermediate cost be privileged?

The formal argument from Forced Coupling (Proposition 3):

At zero query cost, agents query promiscuously. The QUERY signal carries no information about
urgency or unresolved state — there is no cost filtering. Any QUERY is as likely to be noise
as genuine Delta-variable declaration. QRC may be high but the coupling is not load-bearing.

At prohibitive query cost, agents never query. Delta-variables go unresolved. QRC approaches
zero. Coordination collapses.

At intermediate cost, only genuine Delta-variables trigger queries. This selective interrogation
produces stronger statistical dependency between Q and R emissions than either extreme regime.
The prediction is a non-monotonic QRC curve with a peak at an intermediate cost band — not
a monotonically decreasing curve.

This is not merely an empirical prediction. It follows from the Selective Interrogation
mechanism: cost pressure filters out noise, leaving only structurally necessary queries, which
then generate structurally necessary responses. The coupling at intermediate cost is tighter
because it is less diluted by low-stakes communication.

---

## 9. Arms Race and Depth

### 9.1 How do you measure protocol complexity?

Three complementary metrics are required (no single metric is sufficient):

1. **Compression ratio**: LZ77 compression of the per-epoch type history string. Lower
   compressibility = less repetitive = more complex protocol. A mature RESPOND-dominant
   protocol is highly compressible; an escalated adversarial protocol should be less so.

2. **TE network depth**: maximum path length in the directed transfer entropy graph across
   agents and timestep lags. Deeper dependency chains indicate more complex information flow.

3. **Codebook size**: number of distinct signal pattern clusters that carry statistically
   significant mutual information with subsequent action outcomes (measured via cluster
   centroids in PCA space, thresholded at I > 0.05 bits). More codebook entries = more
   differentiated communication vocabulary.

Escalation is confirmed if all three metrics increase monotonically across arms race
generations. Plateau under pressure falsifies the depth growth prediction and suggests that
the current harness has a complexity ceiling set by architectural capacity rather than
structural demand.

---

## 10. Overarching Theoretical Questions

### 10.1 Is Delta a measurable quantity or an interpretive lens?

Delta is a measurable quantity. Operationally: **Delta(agent_i, t)** is the presence of an
unresolved environmental dependency at timestep t — a configuration where agent i cannot
select a reward-maximizing action using only its current local observation, but can do so
given a specific piece of information from another agent's current observation.

This is indirectly but reliably detectable via QRC:
- QRC = 1.0 sustained: all Delta-variables are resolving within the response window
- QRC < 1.0: some Delta-variables are going unresolved; agents are querying but not receiving
  closure (or not querying when they should)
- QRC = 0 at high entropy: no queries are being generated; Delta-variables are not being
  declared

The measure is not a direct read of the agent's internal dependency state — that would require
interpretability tools outside the scope of this study. But it is not post-hoc inference
either. It is a temporal coupling statistic with a clear causal interpretation grounded in
the task structure.

### 10.2 What would falsify the structural account entirely?

The following combination of results would falsify the structural necessity claim:

**All three must hold simultaneously:**

1. The hysteresis experiment (Experiment 2, frozen-policy reversal phase) shows identical
   up/down transition curves — no difference in the tax threshold required to dissolve
   the protocol vs. the threshold required to form it. No structural residue.

2. Agent C ablation (Experiment 6) shows full QRC recovery to pre-ablation levels within
   50 epochs under continued training — no dependency on Agent C's coordination role.
   Coherence is fully substitutable.

3. The campaign (Experiments 1+14 combined) shows a smooth monotonic gradient in QRC and H
   across the full cost range — no clustering, no bimodality, no regime discontinuity.

If all three hold, the observed coordination is consistent with the null model: reward
gradient alignment under communication cost. The Delta-variable framework would remain
a descriptive metaphor but would not constitute a structural necessity result.

Note: any single result alone is not falsifying. The theory predicts near-linear behavior in
low-cost regimes (below the critical band), so monotonic behavior in that region is expected.
The three conditions together would remove the last structural foothold.

### 10.3 Is this generalizable beyond this harness?

The substrate independence claim (Proposition 5 of Delta-Variable Theory) predicts yes, but
the evidence from this harness is necessary rather than sufficient for that claim.

What this study demonstrates: heterogeneous agents under metabolic pressure self-organize
a query-response protocol — including crystallization, phase transitions, and (pending)
structural residue — without being programmed to do so, and with a protocol structure that
is predicted in advance by the theory's five propositions.

The generalization argument rests on the forcing conditions, not the substrate. The conditions
required for interrogative emergence are:
- Finite capacity with genuine depletion risk (energy budget)
- Hidden state across agents (no agent has full observability)
- Cooperative task with environmental coupling (target acquisition requiring cross-agent
  information exchange)
- Cost on information exchange (metabolic Landauer tax on signals)

These conditions are not specific to this architecture. They are present in biological neural
circuits (ATP-limited signaling under partial observability), economic systems under resource
constraint, and human linguistic communities under cognitive load.

The prediction is not "GRU agents will always produce this." The prediction is: "any system
with these structural properties will exhibit interrogative emergence under sufficient
metabolic pressure." Testing this claim across different substrates — continuous action spaces,
non-neural agents, biological or economic data — is the scope of Protocol 3+ and beyond the
current paper. The current study establishes the phenomenon; the generalization claim is a
theoretical prediction awaiting multi-substrate confirmation.

---

## Summary: Where These Answers Go in the Paper

| Question cluster | Paper section |
|---|---|
| 1.1 Null model | Methods — Experimental Design |
| 1.2 Controls | Methods — Conditions and Controls |
| 1.3 Global reward? | Methods — Agent Architecture |
| 2.1–2.4 Measurement | Methods — Metrics and Operationalization |
| 3.1–3.2 Phase behavior | Results — Phase Transition Analysis |
| 4.1–4.2 Locality | Discussion — Locality Experiments (planned) |
| 5.1–5.2 Capacity | Discussion — Capacity Experiments (planned) |
| 6.1–6.2 Representation | Discussion — Limitations and Scope |
| 7.1 Compositionality | Future Work |
| 8.1 Coupling window | Results — Cost Sweep Analysis |
| 9.1 Complexity | Future Work |
| 10.1 Delta measurability | Theory section |
| 10.2 Falsifiability | Discussion — Falsifiability Conditions |
| 10.3 Generalizability | Discussion — Scope and Generalization |
