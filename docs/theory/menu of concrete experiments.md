menu of concrete experiments you can run on your existing harnesses (Synapse + Cross-Origin-Constraint style). Each is phrased as: intervention → prediction → what to measure → pass/fail signature.
A. Phase transition and “crystallization” tests
1.	Tax sweep (critical threshold mapping)
•	Intervention: Sweep communication_tax_rate across a wide range; repeat runs with different seeds.
•	Prediction: A sharp regime change (noise → protocol) within a narrow band.
•	Measure: QRC, TE asymmetry, message entropy, mutual information, survival/viability, time-to-lock.
•	Signature: Bimodal distribution + “cliff” band; stable protocol appears only above/below a critical window (depending on your definition).
2.	Hysteresis test
•	Intervention: Increase tax slowly to induce crystallization, then decrease tax slowly.
•	Prediction: If protocol is structural residue, it persists past the threshold that created it.
•	Measure: Persistence of codebook / QRC under reverse sweep.
•	Signature: Different “up” vs “down” transition points (hysteresis loop).
3.	Metastability under intermittent pressure
•	Intervention: Alternate high-tax and low-tax epochs (square wave).
•	Prediction: Either (a) protocol survives as residue, or (b) it dissolves when pressure relaxes.
•	Measure: Protocol retention, reacquisition time, drift.
•	Signature: Fast reacquisition implies stored structure; slow reacquisition implies it was just optimization chasing reward.
4.	Noise injection at the boundary
•	Intervention: Add controlled channel noise only near the critical tax band.
•	Prediction: True phase transitions are robust; brittle ones collapse.
•	Measure: Probability of crystallization vs noise level; TE/QRC stability.
•	Signature: A stable protocol region should shrink smoothly, not vanish instantly.
B. Locality, non-substitutability, and delegation tests (AnnA stress)
5.	Local failure cannot be offset by distant capacity
•	Intervention: Partition the environment into two localities; starve one side’s capacity while over-provisioning the other.
•	Prediction: Global “score” can look fine while local coherence fails—if locality is binding.
•	Measure: Local survival/viability, local saturation flags, cross-local help attempts.
•	Signature: Local collapse despite global success signals non-substitutability is real.
6.	Broker privilege audit (Agent C as potential violation)
•	Intervention: Give Agent C extra bandwidth or compute, then remove it; compare to symmetric constraints.
•	Prediction: If C becomes a privileged execution path, the system “cheats” through hidden delegation.
•	Measure: TE centrality, dependency graphs, ablation impact, entropy collapse location.
•	Signature: If removing C destroys coherence completely, you likely built a hub, not an emergent local protocol.
7.	Adjacency vs abstraction propagation
•	Intervention: Allow messages only to neighbors (graph adjacency), then allow global broadcast.
•	Prediction: If constraint propagates through adjacency, broadcast should change the qualitative structure.
•	Measure: Topology-conditioned TE, emergence time, protocol complexity.
•	Signature: Broadcast causing “instant coherence” suggests substitution/globalization is doing the work.
C. “Representation not required” vs “representation sneaks in” tests
8.	Memory depth scaling test (Barenholtz claim made empirical)
•	Intervention: Sweep context window / recurrence depth / state memory size.
•	Prediction: Minimum memory depth exists for stable protocol at given hidden-depth setting.
•	Measure: Emergence probability, time-to-lock, error under partial observability.
•	Signature: A knee point: below it no stable protocol; above it stability increases sharply.
9.	Partial observability ladder
•	Intervention: Systematically reduce observability (mask channels, downsample sensors, occlude states).
•	Prediction: As observability drops, required memory/communication cost rises.
•	Measure: Communication volume (even under tax), QRC success, saturation frequency.
•	Signature: Memory/communication compensates for missing state—directly testing “history is needed because you can’t see everything.”
10.	Counterfactual generalization test (combinatorial novelty)
•	Intervention: Train on primitives A and B separately; test on A+B sequences never seen together.
•	Prediction: If sequential structure captures hidden dynamics, novel but physically/behaviorally realizable combos should work.
•	Measure: Viability, compositional success, protocol reuse vs new code emergence.
•	Signature: Successful compositional generalization without retraining.
D. Capacity, saturation, and irreversible loss tests (AnnA core)
11.	Saturation forcing and visible failure
•	Intervention: Force sustained saturation (insufficient oxygen/energy) while preventing “metric masking” (no reward hacks).
•	Prediction: Coherence must fail visibly; delayed collapse doesn’t negate saturation.
•	Measure: Saturation flags, breakdown markers, QRC collapse, recovery probability.
•	Signature: Visible collapse at capacity exceedance; if it stays “stable,” you likely have an escape hatch.
12.	Irreversibility test
•	Intervention: Overload until breakdown, then restore resources to pre-overload levels.
•	Prediction: If loss is irreversible, recovery does not fully restore prior capacity/protocol.
•	Measure: Recovery curve, residual protocol drift, increased future fragility.
•	Signature: Post-event system is permanently altered (capacity/history encoded).
13.	Redistribution ≠ resolution
•	Intervention: Enable “redistribution” actions (e.g., shifting load to other agents/localities) without increasing total capacity.
•	Prediction: You can move pressure, but unresolved deviation persists and resurfaces.
•	Measure: Where/when failure occurs after redistribution; total deviation integral over time.
•	Signature: Delayed failure migration rather than true stabilization.
E. Causality and coupling diagnostics tests (your measurement primitives)
14.	Question cost as coupling primitive (QUERY→RESPONSE lock)
•	Intervention: Sweep query cost and response cost independently.
•	Prediction: There is a window where asking is rare but decisive, producing stronger coupling.
•	Measure: QRC strength, TE directionality, “query selectivity” vs success.
•	Signature: Stronger coupling at intermediate query cost (not at zero, not at infinite).
15.	Protocol ablation taxonomy
•	Intervention: Kill (a) semantics only, (b) timing only, (c) channel only, (d) agent only.
•	Prediction: Load-bearing protocols fail under specific ablations; decorative chatter survives ablation.
•	Measure: Differential performance collapse; TE/QRC collapse patterns.
•	Signature: A “structural dependency fingerprint” unique to the true protocol.
F. Multi-agent arms race and depth-of-hidden-structure tests
16.	Adversarial co-evolution
•	Intervention: Introduce predator/prey roles or competing objectives; allow strategy adaptation.
•	Prediction: Hidden structure deepens; required memory/communication increases; protocols become more abstract.
•	Measure: Protocol complexity growth, memory requirements, emergence time.
•	Signature: Escalation curve: deeper dependencies appear over generations.
17.	Deception pressure (anti-readability)
•	Intervention: Penalize being predictable to the other agent while still requiring coordination with a third party.
•	Prediction: Forces protocols that are locally coherent but externally opaque.
•	Measure: TE patterns (pairwise vs triadic), compression metrics, detectability of “meaning” by an external decoder.
•	Signature: Selective mutual intelligibility without global legibility.
Minimal “starter pack” if you want the highest yield fast
Run these first: (1) Tax sweep, (2) Hysteresis, (6) Broker privilege audit, (11) Saturation visible failure, (14) Query/Response cost sweep.

