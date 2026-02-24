# Backend

FastAPI service and MARL simulation engine for the Dynamic Cross-Origin Constraint harness.

---

## Quick Start

```bash
# From the backend/ directory
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

API available at `http://localhost:8001`. Frontend proxies to this port.

---

## Structure

```
app/                  FastAPI application
  api/                Route handlers
    control.py        Run lifecycle (start, stop, live status)
    loom.py           Neural Loom epoch data endpoint
    runs.py           Run history and metadata
    reports.py        Report generation and download
    interventions.py  Kill switch and perturbation endpoints
    ws.py             WebSocket metrics stream
  db/                 Database session and engine
  models/             SQLAlchemy ORM models (Run, EpochLog, Artifact)
  schemas/            Pydantic request/response schemas
  services/
    run_manager.py    Orchestrates simulation ↔ DB bridge
    hash_chain.py     SHA-256 integrity chain per run
    report_generator.py  PDF/JSON report builder
    weight_exporter.py   Agent checkpoint export

simulation/           MARL engine
  agents/             Three heterogeneous agent architectures
    base_agent.py     Unified output heads; subclasses implement encode()
    agent_a_rnn.py    Agent A — GRU recurrent encoder
    agent_b_cnn.py    Agent B — 3D convolutional encoder
    agent_c_gnn.py    Agent C — Graph attention encoder (broker)
  protocols.py        Protocol registry — P0 (baseline) and P1 (interrogative)
  engine.py           Training loop, epoch orchestration, manifest writer
  environment.py      20×20 grid, dynamic targets
  comm_buffer.py      8-dim float signal vectors with type channel
  training/
    reinforce.py      REINFORCE with Adam
    reward.py         Landauer tax, type multipliers, survival bonus
    temperature.py    Gumbel-Softmax τ schedule (warmup → decay)
  metrics/
    inquiry_metrics.py   QRC, type entropy, query emergence rate
    pca_snapshot.py      Per-epoch 2D signal projections
    energy_roi.py        Information ROI computation
    shannon_entropy.py   Protocol entropy
    transfer_entropy.py  Agent-pair transfer entropy
    mutual_information.py
    zipf_analysis.py
  interventions/      Kill switch and perturbation handlers
  presets/            Environment presets (aerial, deep_sea, social)
  utils/seeding.py    Reproducible seed management

tests/                Pytest suite covering agents, metrics, training, integrity
```

---

## Protocols

| ID | Name | Signal Types | Energy Model |
|----|------|-------------|--------------|
| P0 | Baseline | DECLARE only | Flat Landauer tax |
| P1 | Interrogative | DECLARE · QUERY · RESPOND | Type multipliers: D=1.0× Q=1.5× R=0.8× |

```bash
# Run from backend/
python run_baseline.py --epochs 500 --seed 42
python run_inquiry.py  --epochs 500 --seed 42

# Or directly
python -m simulation.engine --protocol 0 --epochs 500
python -m simulation.engine --protocol 1 --epochs 500
```

Produces a `manifest.json` on completion with crystallization epoch, phase transitions,
and performance statistics.

---

## Preregistered Cost Conditions (P1)

| Condition | QUERY cost | Purpose |
|-----------|-----------|---------|
| Baseline | 1.5× | Primary confirmatory condition |
| Low Pressure | 1.2× | Cost sensitivity lower bound |
| High Pressure | 3.0× | Cost sensitivity upper bound |
| Extreme | 5.0× | Falsification boundary |
| Control | — (P0) | Query-disabled reference |

15 independent seeds per condition · 500 epochs · 10 episodes/epoch

---

## Database

SQLite via SQLAlchemy + Alembic. Default path: `../data/synapse.db`

```bash
alembic upgrade head   # initialise or migrate
```

Tables: `runs`, `epoch_logs`, `artifacts`

---

## Tests

```bash
pytest tests/
```

Covers agent forward pass shapes, CommBuffer type channel, environment dynamics,
hash chain integrity, REINFORCE gradient flow, and metric computations.
