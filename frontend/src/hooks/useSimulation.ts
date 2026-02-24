import { useCallback } from 'react';
import { useSimulationStore } from '../store/simulationSlice';
import { useMetricsStore } from '../store/metricsSlice';
import { createRun, stopRun, pauseRun, resumeRun } from '../api/runs';

export function useSimulation() {
  const { activeRun, config, setActiveRun } = useSimulationStore();
  const { clearEpochs } = useMetricsStore();

  const start = useCallback(async () => {
    clearEpochs();
    const run = await createRun(config);
    setActiveRun(run);
    return run;
  }, [config, setActiveRun, clearEpochs]);

  const stop = useCallback(async () => {
    if (activeRun) {
      await stopRun(activeRun.id);
      setActiveRun({ ...activeRun, status: 'stopped' });
    }
  }, [activeRun, setActiveRun]);

  const pause = useCallback(async () => {
    if (activeRun) {
      await pauseRun(activeRun.id);
      setActiveRun({ ...activeRun, status: 'paused' });
    }
  }, [activeRun, setActiveRun]);

  const resume = useCallback(async () => {
    if (activeRun) {
      await resumeRun(activeRun.id);
      setActiveRun({ ...activeRun, status: 'running' });
    }
  }, [activeRun, setActiveRun]);

  return { activeRun, start, stop, pause, resume };
}
