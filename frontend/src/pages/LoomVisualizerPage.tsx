/**
 * LoomVisualizerPage — Neural Loom Mission Control.
 *
 * Route: /visualizer/loom
 *
 * Three data sources:
 *   1. Control Deck LAUNCH  → starts a live simulation; polls /api/control/live
 *   2. API Run dropdown     → loads a completed DB run via /api/runs/{id}/loom
 *   3. Local JSON upload    → loads a saved report file (run_11_extended_report.json etc.)
 *
 * During Live Mode (polling every 5 s):
 *   - Epoch data accumulates in real-time
 *   - QRC needle, entropy bar, ROI ticker, type distribution all animate
 *   - Scrubber auto-tracks the latest epoch (grab it to inspect any point)
 *   - PCA scatter shows a "streaming" message (PCA requires a complete run)
 *
 * Protocol handling:
 *   - P0: entropy bar = N/A, QRC = N/A, type dist = empty → ROI chart is the
 *         primary signal, contrasted against the P0 baseline reference line
 *   - P1: all four panels active
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { fetchLoomData, parseLoomFile } from '../api/loom';
import type { LoomData } from '../api/loom';
import { startRun, stopRun, fetchLiveStatus } from '../api/control';
import type { RunConfig, RunStatus } from '../api/control';
import ControlDeck from '../components/loom/ControlDeck';
import PCAScatterView from '../components/loom/PCAScatterView';
import TypeEntropyCoolingBar from '../components/loom/TypeEntropyCoolingBar';
import QRCGauge from '../components/loom/QRCGauge';
import ROITicker from '../components/loom/ROITicker';
import TypeDistributionChart from '../components/loom/TypeDistributionChart';

interface RunOption {
  id: number;
  seed: number;
  status: string;
  total_epochs: number;
}

const POLL_INTERVAL_MS = 5000;

export default function LoomVisualizerPage() {
  // ── Data state ───────────────────────────────────────────────────────────
  const [loomData, setLoomData]       = useState<LoomData | null>(null);
  const [selectedEpoch, setSelectedEpoch] = useState(0);
  const [autoAdvance, setAutoAdvance] = useState(false);

  // ── Source selector state ────────────────────────────────────────────────
  const [runs, setRuns]               = useState<RunOption[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [isLoading, setIsLoading]     = useState(false);
  const [loadError, setLoadError]     = useState<string | null>(null);

  // ── Control Deck / live polling state ────────────────────────────────────
  const [runStatus, setRunStatus]     = useState<RunStatus>('idle');
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [totalEpochs, setTotalEpochs] = useState(0);
  const [liveMode, setLiveMode]       = useState(false);
  const [controlError, setControlError] = useState<string | null>(null);
  const [completedRunId, setCompletedRunId] = useState<number | null>(null);

  const liveModeRef = useRef(liveMode);
  liveModeRef.current = liveMode;

  // ── Fetch available DB runs on mount ─────────────────────────────────────
  useEffect(() => {
    axios.get('/api/runs?limit=100')
      .then((res) => setRuns(res.data.runs ?? []))
      .catch(() => { /* backend may be offline */ });
  }, []);

  // ── Live polling loop ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!liveMode) return;

    let active = true;

    const poll = async () => {
      if (!active) return;
      try {
        const data = await fetchLiveStatus();
        if (!active) return;

        setRunStatus(data.status);
        setCurrentEpoch(data.current_epoch);
        setTotalEpochs(data.total_epochs);

        if (data.error) setControlError(data.error);
        if (data.run_id) setCompletedRunId(data.run_id);

        if (data.epochs.length > 0) {
          setLoomData({
            epochs: data.epochs,
            crystallization_epoch: data.crystallization_epoch,
            protocol: data.protocol,
          });
          if (autoAdvance) {
            setSelectedEpoch(data.epochs[data.epochs.length - 1].epoch);
          }
        }

        // Stop polling when run ends
        if (data.status !== 'running') {
          setLiveMode(false);
        }
      } catch {
        // Network error — keep polling
      }
    };

    const id = setInterval(poll, POLL_INTERVAL_MS);
    poll(); // immediate first tick

    return () => {
      active = false;
      clearInterval(id);
    };
  }, [liveMode, autoAdvance]);

  // ── Control Deck callbacks ────────────────────────────────────────────────
  const handleLaunch = useCallback(async (config: RunConfig) => {
    setControlError(null);
    setLoomData(null);
    setSelectedEpoch(0);

    const result = await startRun(config);
    if (!result.ok) {
      setControlError(result.error ?? 'Failed to start run.');
      return;
    }

    setRunStatus('running');
    setTotalEpochs(config.epochs);
    setCurrentEpoch(0);
    setAutoAdvance(true);
    setLiveMode(true);
  }, []);

  const handleStop = useCallback(async () => {
    await stopRun();
    setRunStatus('stopped');
    setLiveMode(false);
  }, []);

  const handleToggleLiveMode = useCallback((enabled: boolean) => {
    setLiveMode(enabled);
    if (enabled) setAutoAdvance(true);
  }, []);

  // ── DB run selector ───────────────────────────────────────────────────────
  const handleRunSelect = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value, 10);
    if (isNaN(id)) return;
    setSelectedRunId(id);
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await fetchLoomData(id);
      setLoomData(data);
      setSelectedEpoch(data.epochs.length > 0 ? data.epochs[data.epochs.length - 1].epoch : 0);
    } catch {
      setLoadError('Failed to load run from API.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── JSON file upload ──────────────────────────────────────────────────────
  const handleFileLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsLoading(true);
    setLoadError(null);
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = parseLoomFile(ev.target?.result as string);
        setLoomData(data);
        setSelectedEpoch(data.epochs.length > 0 ? data.epochs[data.epochs.length - 1].epoch : 0);
      } catch {
        setLoadError('Failed to parse JSON file.');
      } finally {
        setIsLoading(false);
      }
    };
    reader.readAsText(file);
  };

  // ── Derived display values ────────────────────────────────────────────────
  const currentEpochData = loomData?.epochs.find((e) => e.epoch === selectedEpoch) ?? null;
  const maxEpoch = loomData?.epochs.length ? loomData.epochs[loomData.epochs.length - 1].epoch : 0;
  const minEpoch = loomData?.epochs.length ? loomData.epochs[0].epoch : 0;
  const isLiveRun = liveMode || runStatus === 'running';

  return (
    <div className="flex flex-col gap-3 max-w-5xl mx-auto">

      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-blue-400">Neural Loom</h2>
        {loomData && (
          <span className="text-xs text-gray-400 font-mono">
            Protocol {loomData.protocol}
            {loomData.crystallization_epoch !== null
              ? ` · Crystallisation E${loomData.crystallization_epoch}`
              : ' · No crystallisation detected'}
            {isLiveRun && (
              <span className="ml-2 text-red-400 animate-pulse">● LIVE</span>
            )}
            {completedRunId && !isLiveRun && (
              <Link
                to="/history"
                className="ml-3 text-amber-400/80 hover:text-amber-300 underline underline-offset-2"
              >
                → View Run #{completedRunId} in History
              </Link>
            )}
          </span>
        )}
      </div>

      {/* ── Control Deck ─────────────────────────────────────────────────── */}
      <ControlDeck
        runStatus={runStatus}
        currentEpoch={currentEpoch}
        totalEpochs={totalEpochs}
        liveMode={liveMode}
        onLaunch={handleLaunch}
        onStop={handleStop}
        onToggleLiveMode={handleToggleLiveMode}
        errorMsg={controlError}
      />

      {/* ── Source selector (DB run / file) ──────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-4 bg-gray-900 rounded px-3 py-2 text-xs">
        <span className="text-gray-500">Or load archived run:</span>

        {/* DB run dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-gray-500">API:</label>
          <select
            className="bg-gray-800 text-gray-200 border border-gray-700 rounded px-2 py-1 text-xs"
            value={selectedRunId ?? ''}
            onChange={handleRunSelect}
          >
            <option value="">— select —</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                #{r.id} seed={r.seed} ({r.total_epochs}ep) [{r.status}]
              </option>
            ))}
          </select>
        </div>

        {/* JSON file upload */}
        <div className="flex items-center gap-2">
          <label className="text-gray-500">JSON:</label>
          <label className="cursor-pointer bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded px-2 py-1 transition-colors">
            Browse…
            <input type="file" accept=".json" className="hidden" onChange={handleFileLoad} />
          </label>
        </div>

        {isLoading && <span className="text-blue-400 animate-pulse">Loading…</span>}
        {loadError && <span className="text-red-400">{loadError}</span>}
      </div>

      {/* ── Epoch scrubber ────────────────────────────────────────────────── */}
      {loomData && (
        <div className="flex items-center gap-3 bg-gray-900 rounded px-3 py-2">
          <span className="text-xs text-gray-400 whitespace-nowrap font-mono">Epoch</span>
          <input
            type="range"
            min={minEpoch}
            max={maxEpoch}
            value={selectedEpoch}
            onChange={(e) => {
              setAutoAdvance(false);
              setSelectedEpoch(parseInt(e.target.value, 10));
            }}
            className="flex-1 accent-blue-500"
          />
          <span className="text-sm font-mono text-blue-300 w-12 text-right tabular-nums">
            {selectedEpoch}
          </span>
          {liveMode && (
            <button
              className="text-xs text-gray-500 hover:text-blue-400 transition-colors font-mono"
              onClick={() => {
                setAutoAdvance(true);
                if (loomData.epochs.length > 0)
                  setSelectedEpoch(loomData.epochs[loomData.epochs.length - 1].epoch);
              }}
              title="Snap back to latest epoch"
            >
              ↓ latest
            </button>
          )}
        </div>
      )}

      {/* ── 2×2 visualisation grid ───────────────────────────────────────── */}
      {loomData && (
        <div className="grid grid-cols-2 gap-3">

          {/* Top-left: PCA Scatter */}
          <div className="bg-gray-900 rounded p-3 min-h-64">
            {isLiveRun ? (
              <div className="flex flex-col h-full items-center justify-center gap-2">
                <span className="text-xs text-gray-500 text-center">
                  PCA Scatter
                </span>
                <span className="text-xs text-blue-400 animate-pulse text-center">
                  ● Streaming — PCA computed after run completes.
                </span>
                <span className="text-xs text-gray-600 text-center">
                  Load the saved report file to view signal clusters.
                </span>
              </div>
            ) : (
              <PCAScatterView
                points={currentEpochData?.signal_pca ?? null}
                crystallizationEpoch={loomData.crystallization_epoch}
                currentEpoch={selectedEpoch}
              />
            )}
          </div>

          {/* Top-right: Entropy cooling bar + QRC gauge */}
          <div className="bg-gray-900 rounded p-3 flex flex-col gap-5 justify-center">
            <TypeEntropyCoolingBar typeEntropy={currentEpochData?.type_entropy ?? null} />
            <QRCGauge qrc={currentEpochData?.qrc ?? null} />
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 font-mono">
              <span>
                Survival:{' '}
                <span className="text-gray-200">
                  {currentEpochData?.survival_rate?.toFixed(2) ?? '—'}
                </span>
              </span>
              <span>
                ROI:{' '}
                <span className="text-gray-200">
                  {currentEpochData?.inquiry_roi != null
                    ? currentEpochData.inquiry_roi.toFixed(5)
                    : currentEpochData?.energy_roi != null
                    ? currentEpochData.energy_roi.toFixed(5)
                    : '—'}
                </span>
              </span>
              <span>
                τ:{' '}
                <span className="text-gray-200">
                  {loomData.protocol === 1 ? (
                    currentEpochData != null
                      ? `E${selectedEpoch}`
                      : '—'
                  ) : 'P0'}
                </span>
              </span>
              <span>
                Epoch:{' '}
                <span className="text-blue-300">{selectedEpoch}</span>
              </span>
            </div>
          </div>

          {/* Bottom-left: ROI Ticker */}
          <div className="bg-gray-900 rounded p-3 h-52">
            <ROITicker epochs={loomData.epochs} currentEpoch={selectedEpoch} protocol={loomData.protocol} />
          </div>

          {/* Bottom-right: Type Distribution */}
          <div className="bg-gray-900 rounded p-3 h-52">
            <TypeDistributionChart epochs={loomData.epochs} currentEpoch={selectedEpoch} />
          </div>
        </div>
      )}

      {/* ── Empty state ───────────────────────────────────────────────────── */}
      {!loomData && !isLoading && (
        <div className="flex flex-col items-center justify-center h-48 gap-2 text-sm text-gray-600 bg-gray-900 rounded">
          <span>Configure the Control Deck and click</span>
          <span className="font-mono text-blue-500 text-xs">▶ LAUNCH</span>
          <span>or load an archived run from the source selector above.</span>
        </div>
      )}
    </div>
  );
}
