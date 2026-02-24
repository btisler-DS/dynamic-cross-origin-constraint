import { useState } from 'react';
import { useSimulation } from '../../hooks/useSimulation';
import { useSimulationStore } from '../../store/simulationSlice';

export default function RunControlPanel() {
  const { activeRun, start, stop, pause, resume } = useSimulation();
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try { await start(); } finally { setLoading(false); }
  };

  const isRunning = activeRun?.status === 'running';
  const isPaused = activeRun?.status === 'paused';

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h2 className="text-lg font-semibold mb-3">Run Control</h2>

      {activeRun && (
        <div className="mb-3 text-sm space-y-1">
          <p>Run #{activeRun.id} — <span className={`font-medium ${
            isRunning ? 'text-green-400' : isPaused ? 'text-yellow-400' : 'text-gray-400'
          }`}>{activeRun.status}</span></p>
          <p className="text-gray-500">
            Epoch {activeRun.current_epoch} / {activeRun.total_epochs}
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {!activeRun || activeRun.status === 'completed' || activeRun.status === 'stopped' ? (
          <button
            onClick={handleStart}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium disabled:opacity-50"
          >
            {loading ? 'Starting...' : 'Start Run'}
          </button>
        ) : (
          <>
            {isRunning && (
              <button onClick={pause} className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-sm">
                Pause
              </button>
            )}
            {isPaused && (
              <button onClick={resume} className="px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm">
                Resume
              </button>
            )}
            <button onClick={stop} className="px-3 py-2 bg-red-600 hover:bg-red-700 rounded text-sm">
              Stop
            </button>
          </>
        )}
      </div>
    </div>
  );
}
