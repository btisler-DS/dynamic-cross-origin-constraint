# Dynamic Cross-Origin Constraint

**Experimental harness for the Δ-Variable Theory of Interrogative Emergence.**

Multi-agent reinforcement learning system in which three heterogeneous agents (RNN · CNN · GNN)
coordinate under energy constraints. Under Protocol 1, interrogative signal types emerge
spontaneously — agents develop question-asking behaviour because resolving uncertainty is cheaper
than acting blindly.

This repository is the confirmatory experimental platform for the preregistered study:

> *Testing Substrate-Independent Emergence of Interrogative Structures Under Resource Constraints
> in Multi-Agent Coordination Systems*
> DOI: [10.5281/zenodo.18738379](https://doi.org/10.5281/zenodo.18738379)

---

## Structure

```
backend/
  app/           FastAPI API layer (runs, reports, loom, control endpoints)
  simulation/    MARL engine (protocols, agents, environment, metrics)
  run_baseline.py
  run_inquiry.py

frontend/        React + TypeScript UI
  src/pages/     Lab Notebook (Dashboard · History · Compare · Reports)
                 Neural Loom (Control Deck · PCA · QRC · ROI)

docs/
  preregistration.md   Locked preregistration (SHA-256 verified)
  theory/
```

---

## Protocols

| Protocol | Description | Command |
|----------|-------------|---------|
| P0 | Baseline — flat energy tax, no signal types | `python run_baseline.py --epochs 500` |
| P1 | Interrogative Emergence — Gumbel-Softmax type head, variable costs | `python run_inquiry.py --epochs 500` |

---

## Quick Start

```bash
# Backend (Python 3.11+)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload

# Frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Pilot Data

Run 11 (seed=42, 500 epochs, Protocol 1) is included as pilot data in
`frontend/public/run_11_extended_report.json`. Load it in the Neural Loom
to explore the three crystallisation waves and QRC lock-in at E496.

This run is **excluded from confirmatory hypothesis testing** per the preregistration.

---

## Theory

Theoretical grounding: Puchtel (2026), *AnnA: Adaptive, non-neural Axiom* — intelligence as
coherence under pressure. Interrogative emergence is the operational manifestation of regulation
without command under epistemic uncertainty.

---

## Original Development Repository

[Cross-Origin-Constraint](https://github.com/btisler-DS/cross-origin-constraint) — archived
development history and Run 11 pilot artifacts.
