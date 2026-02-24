import { useCallback } from 'react';
import { useWebSocket } from '../api/websocket';
import { useMetricsStore } from '../store/metricsSlice';
import { useSimulationStore } from '../store/simulationSlice';
import type { EpochMetrics } from '../types/metrics';

export function useMetricsStream(runId: number | null) {
  const addEpoch = useMetricsStore((s) => s.addEpoch);
  const updateRunStatus = useSimulationStore((s) => s.updateRunStatus);
  const updateRunEpoch = useSimulationStore((s) => s.updateRunEpoch);

  const onMessage = useCallback(
    (data: EpochMetrics) => {
      addEpoch(data);
      if (runId != null) {
        updateRunStatus(runId, 'running');
        updateRunEpoch(runId, data.epoch);
      }
    },
    [addEpoch, runId, updateRunStatus, updateRunEpoch]
  );

  const onComplete = useCallback(() => {
    if (runId) {
      updateRunStatus(runId, 'completed');
    }
  }, [runId, updateRunStatus]);

  useWebSocket(runId, onMessage, onComplete);
}
