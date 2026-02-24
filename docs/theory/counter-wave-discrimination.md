Competing explanations (mutually distinguishable)
H1) Reward artifact (survival bonus / terminal shaping)

Success delivers a big terminal reward that changes action-selection abruptly, and DECLARE becomes a cheap way to harvest/express that reward regime (or to exploit a learned quirk of the objective). The entropy rebound is then policy diffusion after the “goal is over.”

Prediction: If you remove/reshape the terminal reward, the spike vanishes or changes form.

H2) Phase reset / control-mode switch

Success is a discrete boundary event that triggers a learned “mode transition” (exploration reboot, role renegotiation, protocol re-randomization). DECLARE becomes a mode marker and the entropy rebound is deliberate re-expansion of the search distribution.

Prediction: Spikes persist even if terminal reward is removed, as long as “episode boundary” exists.

H3) Pragmatic content (coordination speech act)

DECLARE is doing real work: on success it signals “state achieved / commit to new regime / stop querying / stop spending.” The entropy rebound is not noise; it’s the system re-opening degrees of freedom once viability is secure (pressure relieved → regulation relaxes → structure loosens).

Prediction: If you keep pressure on after “success,” the rebound should not occur (or should be delayed), because the system can’t afford relaxation.

The fastest discriminating experiments to run on your harness
1) Terminal reward ablation

Change: Set survival bonus to 0 (or distribute it smoothly across the final N steps).

Measure: DECLARE rate at success; entropy trajectory in last K steps.

Interpretation:

Spike disappears → strong support for H1

Spike remains → H2/H3 more likely

2) Boundary without reward

Change: Keep episode termination at full-survival, but give no terminal bonus (or identical bonus on failure too).

Measure: DECLARE spike timing relative to termination; entropy rebound.

Interpretation: Boundary alone causing spike → H2.

3) Reward without boundary

Change: Don’t end the episode on success; instead give the same “success reward” but continue the environment for M more steps under identical conditions.

Measure: Does DECLARE spike at reward time? Does entropy rebound happen immediately or only after boundary?

Interpretation:

Spike follows reward time → H1

Spike follows boundary/termination time → H2

Spike occurs but rebound depends on pressure → points to H3

4) Keep pressure after success

Change: On “success,” do not relax constraints—increase tax/oxygen drain for the next M steps (or keep threats active).

Measure: Does entropy still rebound? Does DECLARE still spike?

Interpretation:

Rebound suppressed/delayed → H3 (pressure relief drives rebound)

Rebound unaffected → H1/H2

5) DECLARE cost sweep

Change: Make DECLARE expensive (or cap it), and separately make it free.

Measure: Is the spike robust to cost? Do agents substitute another token/act?

Interpretation:

Cost-sensitive spike → H1 (instrumental exploitation)

Cost-insensitive spike + substitution → H2/H3 (structural speech act / mode marker)

6) Privilege test: does DECLARE change any state?

Change: Run two conditions:

DECLARE is a no-op token (pure message)

DECLARE triggers an environment-visible toggle (e.g., “commit” flag, shared memory marker, role lock)

Measure: Does performance improve only when DECLARE has real consequences?

Interpretation: If performance depends on consequential DECLARE → supports H3.

What to log (so the answer is unambiguous)

For each success episode (E202/E381/E390-like), capture a K-step window around the event:

Token rates by type (DECLARE / QUERY / RESPONSE / other)

Policy entropy and message entropy separately

Reward components (dense vs terminal)

Tax/energy state

TE/QRC before vs after the spike

“Action variance” (are they thrashing or renegotiating?)

A key separation: policy entropy vs message entropy.
If policy entropy stays low but message entropy rebounds, that suggests “speech diversification” not behavioral collapse—very different interpretation.

The single most decisive test

If you only run one: Reward-without-boundary (Experiment #3).

Because it cleanly asks: is the spike tied to reward delivery or to episode termination / mode boundary?