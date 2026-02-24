/**
 * ControlDeck — Mission Control panel for the Neural Loom.
 *
 * Collapsible header above the visualisation grid. Provides:
 *   - Protocol selector (P0 Baseline / P1 Interrogative)
 *   - Config inputs: epochs, episodes, seed
 *   - Launch / Stop buttons
 *   - Status bar with progress and Live Mode toggle
 */

import { useState } from 'react';
import type { RunConfig, RunStatus } from '../../api/control';

interface Props {
  runStatus: RunStatus;
  currentEpoch: number;
  totalEpochs: number;
  liveMode: boolean;
  onLaunch: (config: RunConfig) => void;
  onStop: () => void;
  onToggleLiveMode: (enabled: boolean) => void;
  errorMsg: string | null;
}

const STATUS_COLOUR: Record<RunStatus, string> = {
  idle:      'text-gray-500',
  running:   'text-blue-400',
  completed: 'text-green-400',
  stopped:   'text-yellow-400',
  failed:    'text-red-400',
};

const STATUS_BAR_COLOUR: Record<RunStatus, string> = {
  idle:      'bg-gray-600',
  running:   'bg-blue-500',
  completed: 'bg-green-500',
  stopped:   'bg-yellow-500',
  failed:    'bg-red-500',
};

export default function ControlDeck({
  runStatus,
  currentEpoch,
  totalEpochs,
  liveMode,
  onLaunch,
  onStop,
  onToggleLiveMode,
  errorMsg,
}: Props) {
  const [open, setOpen] = useState(true);
  const [protocol, setProtocol] = useState(1);
  const [epochs, setEpochs] = useState(100);
  const [episodes, setEpisodes] = useState(10);
  const [seed, setSeed] = useState(42);

  const isRunning = runStatus === 'running';
  const progress = totalEpochs > 0 ? (currentEpoch + 1) / totalEpochs : 0;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded overflow-hidden">

      {/* ── Title bar ─────────────────────────────────────────────────────── */}
      <button
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-800 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-xs font-mono font-bold tracking-widest text-gray-300">
          ⚙ CONTROL DECK
        </span>
        <span className="text-xs text-gray-600">{open ? '▲ collapse' : '▼ expand'}</span>
      </button>

      {/* ── Config form ───────────────────────────────────────────────────── */}
      {open && (
        <div className="px-4 pt-2 pb-4 border-t border-gray-800 flex flex-col gap-4">

          {/* Protocol selector */}
          <div className="flex flex-col gap-1.5">
            <span className="text-xs text-gray-500 uppercase tracking-widest">Protocol</span>
            <div className="flex gap-2">
              <button
                onClick={() => setProtocol(0)}
                disabled={isRunning}
                className={`flex-1 py-2 px-3 rounded text-xs font-mono font-bold border transition-colors text-left ${
                  protocol === 0
                    ? 'bg-gray-700 border-gray-400 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-300'
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                <div>P0 · BASELINE</div>
                <div className="text-[10px] font-normal mt-0.5 opacity-60">Flat tax · no signal types</div>
              </button>
              <button
                onClick={() => setProtocol(1)}
                disabled={isRunning}
                className={`flex-1 py-2 px-3 rounded text-xs font-mono font-bold border transition-colors text-left ${
                  protocol === 1
                    ? 'bg-blue-950 border-blue-400 text-blue-200'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-blue-700 hover:text-blue-300'
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                <div>● P1 · INTERROGATIVE</div>
                <div className="text-[10px] font-normal mt-0.5 opacity-60">Questions cost extra · agents discover value</div>
              </button>
            </div>
          </div>

          {/* Numeric params */}
          <div className="grid grid-cols-3 gap-3">
            {(
              [
                { label: 'Epochs',   hint: 'Training cycles',  value: epochs,   set: setEpochs,   min: 1,  max: 2000  },
                { label: 'Episodes', hint: 'Attempts per cycle', value: episodes, set: setEpisodes, min: 1,  max: 50    },
                { label: 'Seed',     hint: 'Reproducibility key', value: seed,   set: setSeed,     min: 0,  max: 99999 },
              ] as const
            ).map(({ label, hint, value, set, min, max }) => (
              <div key={label} className="flex flex-col gap-1">
                <span className="text-xs text-gray-500">{label}</span>
                <input
                  type="number"
                  min={min}
                  max={max}
                  value={value}
                  onChange={(e) => set(Number(e.target.value))}
                  disabled={isRunning}
                  className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 font-mono w-full disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:border-blue-600"
                />
                <span className="text-[10px] text-gray-600">{hint}</span>
              </div>
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => onLaunch({ epochs, episodes, seed, protocol })}
              disabled={isRunning}
              className="flex-1 py-2 bg-blue-700 hover:bg-blue-600 active:bg-blue-800 disabled:bg-gray-800 disabled:text-gray-600 text-white text-xs font-mono font-bold rounded transition-colors"
            >
              ▶ LAUNCH {protocol === 0 ? 'BASELINE' : 'INQUIRY'}
            </button>
            <button
              onClick={onStop}
              disabled={!isRunning}
              className="px-4 py-2 bg-red-950 hover:bg-red-900 active:bg-red-800 disabled:bg-gray-800 disabled:text-gray-600 text-red-300 text-xs font-mono font-bold rounded border border-red-800 disabled:border-gray-700 transition-colors"
            >
              ■ STOP
            </button>
          </div>
        </div>
      )}

      {/* ── Status bar — always visible ───────────────────────────────────── */}
      <div className="px-4 py-2 bg-gray-950 border-t border-gray-800 flex items-center gap-3 min-h-[2.25rem]">

        {/* Status label */}
        <span
          className={`text-xs font-mono font-bold tracking-widest ${STATUS_COLOUR[runStatus]} ${
            isRunning ? 'animate-pulse' : ''
          }`}
        >
          {runStatus.toUpperCase()}
        </span>

        {/* Progress */}
        {runStatus !== 'idle' && (
          <>
            <span className="text-xs text-gray-500 font-mono whitespace-nowrap">
              E{currentEpoch} / {totalEpochs}
            </span>
            <div className="flex-1 bg-gray-800 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${STATUS_BAR_COLOUR[runStatus]}`}
                style={{ width: `${Math.min(progress * 100, 100).toFixed(1)}%` }}
              />
            </div>
          </>
        )}

        {runStatus === 'idle' && <span className="flex-1" />}

        {/* Error */}
        {errorMsg && (
          <span
            className="text-xs text-red-400 truncate max-w-[16rem]"
            title={errorMsg}
          >
            ⚠ {errorMsg}
          </span>
        )}

        {/* Live Mode toggle */}
        <button
          onClick={() => onToggleLiveMode(!liveMode)}
          title={liveMode ? 'Disable live polling' : 'Enable live polling (5 s)'}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold border transition-colors ${
            liveMode
              ? 'bg-red-950 border-red-600 text-red-300'
              : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              liveMode ? 'bg-red-400 animate-pulse' : 'bg-gray-600'
            }`}
          />
          LIVE
        </button>
      </div>
    </div>
  );
}
