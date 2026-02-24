# Frontend

React + TypeScript interface for the Dynamic Cross-Origin Constraint harness.
Two operating modes: **Lab Notebook** (📓) and **Neural Loom** (🔬).

---

## Quick Start

```bash
# From the frontend/ directory
npm install
npm run dev
# → http://localhost:5173
```

Requires the backend running on port 8001. All `/api/*` requests are proxied via Vite.

---

## Structure

```
src/
  pages/
    DashboardPage.tsx       Live run control and real-time metrics grid
    HistoryPage.tsx         Completed run browser with hash chain verification
    ComparisonPage.tsx      Side-by-side run comparison (entropy, ROI, survival)
    ReportPage.tsx          PDF / JSON report download
    SettingsPage.tsx        Configuration presets
    LoomVisualizerPage.tsx  Neural Loom — epoch scrubber + 2×2 visualisation grid

  components/
    loom/
      ControlDeck.tsx         Protocol selector, run config, Launch/Stop, status bar
      PCAScatterView.tsx       D3 scatter — signal clusters coloured by type (D/Q/R)
      TypeEntropyCoolingBar.tsx  Entropy bar — orange (H=1.585) → blue (H=0)
      QRCGauge.tsx             SVG arc gauge — Query-Response Coupling 0→1
      ROITicker.tsx            Recharts line — P1 ROI vs P0 baseline reference
      TypeDistributionChart.tsx  D/Q/R stacked area over epoch history

    charts/                   Recharts wrappers for Notebook mode
      EntropyChart.tsx
      EnergyROIChart.tsx
      SurvivalChart.tsx
      SignalHeatmap.tsx
      TransferEntropyChart.tsx
      MutualInfoChart.tsx
      ZipfChart.tsx

    dashboard/                Live run panels
    comparison/               Run selector and diff views
    reports/                  Download buttons and preview
    integrity/                Hash chain viewer
    interventions/            Kill switch and perturbation controls
    Tooltip.tsx               Reusable ? tooltip component

  api/                        Axios wrappers for all backend endpoints
    client.ts                 Base Axios instance (port 8001)
    control.ts                Start / stop / live status
    loom.ts                   Loom epoch data + JSON file parser
    runs.ts                   Run history and metadata
    reports.ts                Report generation
    interventions.ts          Kill switch and perturbations
    websocket.ts              Real-time metrics stream

  hooks/
    useSimulation.ts          Run lifecycle state
    useMetricsStream.ts       WebSocket metrics subscription
    useRunComparison.ts       Multi-run comparison state

  store/
    simulationSlice.ts        Run state (Zustand)
    metricsSlice.ts           Live metrics buffer

  types/                      Shared TypeScript interfaces
```

---

## Modes

### 📓 Lab Notebook
Dashboard · History · Compare · Reports

Tracks completed runs stored in the database. The Dashboard streams live metrics
during an active run via WebSocket. History shows the hash chain integrity badge
for each completed run.

### 🔬 Neural Loom
Route: `/visualizer/loom`

Post-hoc analysis of a single run. Three data sources:
- **Control Deck LAUNCH** — starts a live simulation, polls `/api/control/live` every 5 s
- **API dropdown** — loads a completed run from the database via `/api/runs/{id}/loom`
- **JSON upload** — loads a saved report file (e.g. `run_11_extended_report.json`)

Four visualisation panels update as the epoch scrubber moves:
| Panel | Shows |
|-------|-------|
| PCA Scatter | Signal vector clusters coloured by type; crystallisation pulse at phase transition |
| Entropy + QRC | Type entropy cooling bar + Query-Response Coupling gauge |
| ROI Ticker | Protocol 1 ROI vs Protocol 0 baseline reference line |
| Type Distribution | D / Q / R stacked area across all epochs to current |

---

## Pilot Data

`public/run_11_extended_report.json` — Run 11 (seed=42, 500 epochs, Protocol 1).
Load via the Neural Loom JSON upload to explore the three crystallisation waves
and QRC lock-in. Excluded from confirmatory hypothesis testing per the preregistration.

---

## Build

```bash
npm run build   # outputs to dist/
```

Production deployment uses Nginx — see `nginx.conf` and `Dockerfile`.
