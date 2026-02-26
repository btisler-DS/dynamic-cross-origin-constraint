# Build Report — 2026-02-26

**Project**: The Δ-Variable Theory of Interrogative Emergence
**Repository**: https://github.com/btisler-DS/dynamic-cross-origin-constraint
**OSF**: https://osf.io/f6gxc — DOI: 10.17605/OSF.IO/F6GXC
**Preregistration**: https://doi.org/10.5281/zenodo.18738379
**Author**: Tisler, B.
**Build period**: 2026-02-23 to 2026-02-26 (13 commits, 4 days)

---

## 1. Executive Summary

This report covers the complete build of the `dynamic-cross-origin-constraint` harness from
initial commit to confirmatory campaign completion. The harness tests the Δ-Variable Theory
of Interrogative Emergence: that question-asking structures arise as mathematically necessary
solutions to uncertainty management under resource constraints, independent of cognitive
substrate.

**Confirmatory campaign outcome (2026-02-26)**:
- 75 runs completed, 0 failures
- **P1 confirmed**: Protocol 1 crystallizes in 54 of 60 experimental runs (90%); Protocol 0
  produces zero crystallization across all 15 control runs
- **P2 confirmed**: Query-Response Coupling (QRC) increases monotonically with query cost up
  to the high-pressure condition (q=3.0, QRC=0.969), then drops at extreme pressure
  (q=5.0, QRC=0.937), identifying a non-monotonic coupling window
- **P3–P5**: Require next experimental phase (hysteresis sweep, Agent C ablation)

---

## 2. Scope

### 2.1 What Was Built

The full harness consists of three integrated layers:

| Layer | Description |
|---|---|
| **Simulation engine** | Multi-agent RL environment with Protocol registry, three agent architectures, Landauer tax reward model |
| **Backend API** | FastAPI service with run lifecycle management, database persistence, hash chain integrity, PDF/JSON reporting |
| **Frontend UI** | React application with two operating modes: Lab Notebook (run history, comparison, reports) and Neural Loom (epoch-by-epoch visualization) |

Plus supporting infrastructure:
- Protocol 0 / Protocol 1 CLI wrappers
- 75-run campaign orchestrator (`run_campaign.py`)
- Manifest writer (per-run JSON with crystallization detection)
- PCA signal snapshot collector (per-epoch 2D projections)
- Full test suite (6 pytest modules)
- Public OSF project, Zenodo preregistration, GitHub repository

### 2.2 What Was Not Built

The following items are scoped for subsequent experimental phases:
- Protocol 2 (8 query types, variable cost, Zipf optimization)
- Hysteresis sweep (frozen-policy tax reversal, Experiment 2)
- Agent C ablation runs (5 seeds, Experiment 6)
- Counter-wave discrimination runs (H1/H2/H3, Experiments 3–5)
- CUDA-accelerated training (CPU-only campaign completed)
- Formal paper Results section (in preparation)

---

## 3. Architecture

### 3.1 Simulation Engine

**Location**: `backend/simulation/`

The simulation engine implements a 20×20 grid environment where three heterogeneous agents
must coordinate dynamic target acquisition under metabolic pressure.

**Agent architectures** (`backend/simulation/agents/`):

| Agent | Architecture | Role |
|---|---|---|
| Agent A | GRU recurrent (RNN) | Sequential pattern encoding |
| Agent B | 3D convolutional (CNN) | Volumetric/spatial encoding |
| Agent C | Graph attention network (GNN) | Relational encoding; empirically the Weaver (coordination broker) |

All agents inherit from `BaseAgent` which centralises the output heads:
- `signal_mu`: 8-dim continuous signal vector (Gaussian reparameterisation)
- `action_head`: 5-action discrete policy
- `type_head`: 3-way signal type classifier (DECLARE / QUERY / RESPOND)

Subclasses implement only `encode()`, returning the post-fusion trunk tensor.

**Protocol registry** (`backend/simulation/protocols.py`):

Two concrete protocol classes share a `ProtocolBase` interface:

- **Protocol 0** (baseline): flat communication tax, no type gradient, type_head frozen to
  DECLARE. Replicates Run 10 pre-study behaviour.
- **Protocol 1** (interrogative): Gumbel-Softmax type sampling with differential cost
  multipliers (DECLARE=1.0×, QUERY=1.5×, RESPOND=0.8×), full type_head gradient.

Temperature schedule: warmup τ=1.0 for 20 epochs, exponential decay to τ=0.1.

**CommBuffer** (`backend/simulation/comm_buffer.py`):
8-dim float signal vectors with a separate `_type_buffer` channel for Protocol 1 type
integers. Broadcast and reset between episodes within each epoch.

**Training** (`backend/simulation/training/`):
REINFORCE with Adam optimizer. Critical implementation note: `store_outcome()` must record
`combined_log_prob = action_log_prob + type_log_prob` — omitting the type term produces
zero gradient on the type_head (silent failure mode discovered and fixed in pilot).

**Manifest writer** (`engine._write_manifest()`):
On run completion writes `manifest.json` per seed containing: protocol ID, seed, cost
parameters, final metrics (survival, target rate, energy ROI, type entropy, QRC),
crystallization epoch (first epoch where H < 0.95 for 5 consecutive epochs), detected phase
transitions, and performance stats (avg/max survival over the run).

**PCA snapshots** (`backend/simulation/metrics/pca_snapshot.py`):
Per-epoch: samples up to 20 signal vectors per agent, fits a global PCA across all epochs,
projects each epoch's sample to 2D. Result stored in `epoch_metrics['signal_pca']` for
Neural Loom rendering.

### 3.2 Backend API

**Location**: `backend/app/`
**Port**: 8001
**Framework**: FastAPI with SQLAlchemy + SQLite, Alembic migrations

**Endpoints**:

| Route | Purpose |
|---|---|
| `POST /api/control/start` | Launch run; returns `run_id` |
| `GET /api/control/{run_id}/status` | Live polling for run state |
| `WS /api/ws/{run_id}` | WebSocket real-time metrics stream |
| `GET /api/runs/` | Run history list |
| `GET /api/runs/{id}` | Run metadata + hash chain |
| `GET /api/runs/{id}/loom` | Full epoch list for Neural Loom (type_entropy, QRC, D/Q/R, ROI, signal_pca) |
| `GET /api/reports/{id}` | PDF / JSON report download |
| `POST /api/interventions/kill` | Stop a running experiment |

**Hash chain integrity** (`backend/app/services/hash_chain.py`):
Each epoch log is SHA-256 hashed with the previous epoch's hash as a salt, creating a
tamper-evident chain. Displayed as a verification badge in the UI History page.

**Report generation** (`backend/app/services/report_generator.py`):
Builds PDF (ReportLab) and JSON reports from epoch logs. JSON report format mirrors
`run_11_extended_report.json` for backward compatibility with the Neural Loom file upload.

### 3.3 Frontend

**Location**: `frontend/src/`
**Framework**: React 18, TypeScript, Vite, Tailwind CSS
**State**: Zustand (`simulationSlice`, `metricsSlice`)
**Charts**: Recharts (line/area charts), D3 v7 (PCA scatter)

**Two operating modes** (distinguished by nav icon and `ModeBadge`):

**Lab Notebook** (📓 amber):
- Dashboard: live run control with ParameterForm + real-time metrics grid
- History: completed run browser with hash chain verification badge
- Compare: side-by-side protocol comparison (entropy, ROI, survival)
- Reports: PDF/JSON download interface

**Neural Loom** (🔬 cyan):
- ControlDeck: protocol selector, config form, Launch/Stop, field helper text with
  plain-English protocol descriptions
- Epoch scrubber (0 → max_epoch range slider)
- 2×2 visualisation grid:
  - **PCAScatterView** (D3): signal clusters coloured by type (D=gray, Q=amber, R=blue);
    Agent C uses diamond shape; ring-pulse animation at crystallisation epoch; "Phase
    Transition Detected" toast
  - **TypeEntropyCoolingBar**: horizontal bar interpolating orange (H=1.585) → blue (H=0)
  - **QRCGauge**: SVG arc gauge with colour zones (red/yellow/green); pulse at QRC=1.000
  - **ROITicker** (Recharts): Protocol 1 ROI vs Protocol 0 baseline reference line
- `? ` tooltips on QRC, type entropy, and PCA panels

**Pilot data**: `frontend/public/run_11_extended_report.json` (142 KB) — Run 11 seed=42,
500 epochs, Protocol 1. Loaded by Neural Loom when no live run is active, providing
immediate visualisation of the pilot phase transition sequence.

---

## 4. Campaign Execution

### 4.1 Design

The confirmatory campaign was fully specified in the preregistration
(DOI: 10.5281/zenodo.18738379, SHA-256:
`7edc9113e39afb2dce430eb77802d5a6c10988e269eb823ae30e5508b12a8d6a`).

- **5 cost conditions**: low_pressure (q=1.2), baseline (q=1.5), high_pressure (q=3.0),
  extreme (q=5.0), control (Protocol 0 flat tax)
- **15 independent seeds per condition** (seeds 0–14)
- **500 epochs per run**, 10 episodes per epoch
- **75 total runs**, orchestrated by `run_campaign.py`

Communication costs: DECLARE=1.0×, QUERY=1.5× (or q), RESPOND=0.8×

### 4.2 Execution

The campaign ran on CPU across two sessions (2026-02-24 to 2026-02-26). All 75 runs
completed; 0 failures.

### 4.3 Results

| Condition | Q cost | QRC | Type Entropy (H) | Survival | Crystallized | Avg onset |
|---|---|---|---|---|---|---|
| Low pressure | 1.2× | 0.810 | 0.944 | 0.167 | 11/15 | epoch 130 |
| Baseline | 1.5× | 0.887 | 0.946 | 0.147 | 14/15 | epoch 152 |
| High pressure | 3.0× | 0.969 | 0.746 | 0.180 | 14/15 | epoch 88 |
| Extreme | 5.0× | 0.937 | 0.537 | 0.067 | 15/15 | epoch 41 |
| Control (P0) | flat | — | — | 0.093 | 0/15 | — |

**Metric definitions**:
- **QRC**: Query-Response Coupling = P(RESPOND within 3 timesteps | QUERY at t), averaged
  over the final 50 crystallised epochs for conditions that crystallised
- **H**: Shannon entropy of D/Q/R type distribution (bits); max = 1.585 bits (uniform)
- **Survival**: fraction of episodes where ≥1 agent reaches target
- **Crystallized**: runs where H < 0.95 for ≥5 consecutive epochs
- **Avg onset**: mean epoch of first crystallisation across crystallised runs

### 4.4 Key Findings

**P1 — Confirmed.** Interrogative protocols emerge under differential cost (Protocol 1)
and do not emerge under flat tax (Protocol 0). The 90% crystallisation rate vs 0% in
controls is stark. The flat-tax baseline confirms that type-differentiated signalling
requires cost gradient incentive — it does not appear by chance.

**P2 — Confirmed with coupling window.** QRC and type specialisation (H reduction)
increase with query cost up through the high-pressure condition (q=3.0, QRC=0.969).
At extreme pressure (q=5.0), QRC drops to 0.937 and survival collapses to 0.067 — below
the Protocol 0 control (0.093). This identifies the **metabolic saturation boundary**: the
point at which query cost exceeds the informational value of interrogative coupling,
causing agents to suppress queries entirely and attempt uncoordinated action.

The non-monotonic QRC curve (peak at q=3.0, decline at q=5.0) was predicted by the theory
(Experiment 14 coupling window analysis) and is confirmed here. This is a qualitative
signature of the theory: smooth reward optimisation would produce monotonic curves; a
non-monotonic window is a structural prediction of the Δ-variable framework.

**P3–P5 — Pending.** These require:
- P3 (hysteresis): frozen-policy tax reversal experiment — does crystallised protocol
  persist when query cost is reduced below formation threshold?
- P4 (no privileged hub): Agent C ablation — does removing Agent C dissolve or redirect
  the coordination structure?
- P5 (substrate independence): cross-architecture QRC comparison across seeds — do A, B,
  C converge on the same interrogative strategy at the single-agent level?

**Pilot data (exploratory, pre-preregistration)**:
Run 11 (seed=42, Protocol 1) established the full phenomenology:
- Three crystallisation waves (E21, E57, E128–E141)
- Counter-wave phenomenon: full-survival events (surv=1.00) trigger transient DECLARE
  spikes, temporarily reversing H reduction, before the system re-enters the crystallised
  regime
- QRC persistently ≥0.95 from epoch 280 onward
- Final equilibrium: R≈0.64, D≈0.20, Q≈0.16 — not a fixed point but a limit cycle

---

## 5. Theory Documents

All theory documents are in `docs/theory/`.

| Document | Purpose |
|---|---|
| `README.md` | Core claim, five propositions, theoretical grounding (AnnA, IBN), paper structure |
| `preregistration.md` | Locked preregistration (SHA-256 verified) |
| `counter-wave-discrimination.md` | Three hypotheses for full-survival DECLARE spikes + 6 discriminating experiments |
| `menu of concrete experiments.md` | 17 post-confirmatory experiments across 6 categories |
| `foundational-questions-answered.md` | Paper-ready answers to 10 question clusters: null model, QRC privilege, crystallisation definition, falsifiability conditions, locality/capacity/representation/compositionality, coupling window, arms race, generalisability |
| `ants-implicit-delta.md` | Implicit vs explicit Δ analysis: Stigmergic Coupling Index (SCI) definition, Reid et al. (2015, PNAS) hysteresis evidence, minimal Proposition 1 revision, draft Discussion Section 6.3 |
| `response-to-anna-assessment.md` | Formal scope boundary with AnnA framework: what to adopt (constraint-bearing residue, regulation without command, pressure redistribution) and what not to (full axiom system) |

### 5.1 Theoretical Core

The **Δ-Variable** is defined as an explicitly represented, unresolved dependency variable
that requires external information for resolution and creates mandatory coupling between
systems. The invariant statement spanning implicit (ant stigmergy) and explicit (MARL
signal tokens) substrates: *"Δ is structural dependency under constraint."*

**Five propositions** (Tisler 2026):
1. **Structural Necessity**: In any system with internal uncertainty states, bounded
   resources, and coupling opportunities, Δ-variables emerge necessarily — not as an
   optimised strategy but as the minimum residue of unresolved constraint.
2. **Cost-Benefit Optimisation**: The rate of Δ-variable generation is a decreasing
   function of the marginal cost-to-information-value ratio.
3. **Forced Coupling**: A Δ-variable in one system creates a structural obligation in the
   receiving system — silence is not neutral; it propagates unresolved dependency.
4. **Silent Collapse Prevention**: Systems without mechanisms for Δ-variable externalisation
   undergo silent collapse — internal uncertainty accumulates without coordination signal.
5. **Substrate Independence**: The mathematical structure of interrogative protocols is
   independent of the physical substrate implementing them.

**Falsifiability** (three-part, from `foundational-questions-answered.md`):
The theory fails if:
(1) No hysteresis — crystallised protocols dissolve immediately when pressure is reduced
    below formation threshold (Experiment 2);
(2) Full Agent C recovery — C-ablated systems reach equivalent coordination within 50
    epochs, showing no structural role for the relational broker (Experiment 6);
(3) Smooth gradient — no phase transition signature; entropy decreases as a smooth
    monotonic function of training time (rejectable from existing Run 11 data).

---

## 6. Public Infrastructure

| Asset | Location | Status |
|---|---|---|
| GitHub repository | https://github.com/btisler-DS/dynamic-cross-origin-constraint | Public, 13 commits |
| Zenodo preregistration | https://doi.org/10.5281/zenodo.18738379 | Locked before campaign |
| OSF project | https://osf.io/f6gxc | Public, wiki updated 2026-02-26 |
| Campaign data | `data/campaign/` (75 manifests) | In repo, commit cc1dcce |
| Pilot report | `frontend/public/run_11_extended_report.json` | In repo, 142 KB |

**OSF wiki** (updated 2026-02-26 via API version creation, wiki version 4):
Contains project status, resources table, five preregistered predictions with campaign
outcome annotations (P1/P2 confirmed, P3–P5 pending), full campaign results table, scope
statement (confirmatory vs exploratory), and citation block.

---

## 7. Commit History

| Hash | Date | Description |
|---|---|---|
| `d5e1571` | 2026-02-23 | Initial harness — Protocol registry, Notebook + Microscope UI |
| `1cca620` | 2026-02-23 | Add docs/README.md |
| `8f1aebd` | 2026-02-23 | Add docs/theory/README.md — Δ-Variable Theory |
| `a6fd260` | 2026-02-23 | Add backend/README.md |
| `e334c78` | 2026-02-24 | Add frontend/README.md |
| `ef24371` | 2026-02-24 | Move experiment menu to docs/theory/ |
| `271887b` | 2026-02-24 | Add counter-wave-discrimination.md |
| `5882968` | 2026-02-24 | Add campaign runner and cost parameterization |
| `d47b695` | 2026-02-24 | Update docs/theory/README.md — full theory index |
| `ac87a0e` | 2026-02-24 | Add response-to-anna-assessment.md |
| `7d26aed` | 2026-02-25 | Add foundational-questions-answered.md |
| `ec1d663` | 2026-02-25 | Add ants-implicit-delta.md |
| `cc1dcce` | 2026-02-26 | Add campaign results: 75 runs, 5 conditions × 15 seeds × 500 epochs |

---

## 8. File Count Summary

| Component | Count |
|---|---|
| Backend Python files | ~69 (simulation, app, services, tests, runners) |
| Frontend TypeScript/TSX files | ~48 (pages, components, hooks, stores, API) |
| Theory/docs markdown files | 9 |
| Campaign manifest files | 75 + 1 summary |
| Configuration files | ~12 (Makefile, docker-compose, pyproject.toml, package.json, etc.) |
| **Total tracked files** | **~214** |

---

## 9. Open Items

### Immediate
- **Revoke OSF API token**: Token `0TguZGBXf...` was used in this session and should be
  regenerated from osf.io account settings.
- **CUDA installation**: Campaign ran CPU-only. Install PyTorch with CUDA before next
  batch of experiments to reduce epoch wall-clock time.

### Next experiments (Protocol 2 phase)
- **Experiment 2** — Hysteresis sweep: freeze agent policies at crystallisation epoch,
  then reduce query cost to q=1.2. Measure H and QRC over 100 subsequent epochs.
  Confirms or falsifies P3.
- **Experiment 6** — Agent C ablation: disable Agent C's type_head gradient (frozen to
  DECLARE) in 5 seeds of the baseline condition. Compare crystallisation rate and QRC.
  Confirms or falsifies P4.
- **Experiments 3–5** — Counter-wave discrimination: H1 (declarative success signal),
  H2 (exploration reset), H3 (pragmatic recalibration). Use Run 11 extended data plus
  one new Protocol 1 run.
- **Protocol 2** — 8 query types with variable costs. Zipf coefficient target for query
  frequency distribution. Agent C QUERY role expected to specialise further.

### Paper
- Draft Results section using campaign data (tables in Section 4.3 above are paper-ready)
- Draft Discussion 6.3 from `ants-implicit-delta.md` (implicit vs explicit Δ)
- Related Work: IBN prohibition arguments, AnnA deductive grounding, Elicit review citations
- Target journal: TBD

---

*Build report generated 2026-02-26. All data, code, and preregistration materials are
publicly available under CC BY-NC 4.0.*
