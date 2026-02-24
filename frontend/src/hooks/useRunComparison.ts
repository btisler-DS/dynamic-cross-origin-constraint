import { useCallback } from 'react';
import { useMetricsStore } from '../store/metricsSlice';
import { getEpochs } from '../api/runs';
import type { EpochMetrics } from '../types/metrics';

export function useRunComparison() {
  const { comparisonRuns, setComparisonData, clearComparison } = useMetricsStore();

  const loadRun = useCallback(
    async (runId: number) => {
      const data = await getEpochs(runId);
      const epochs = data.map((d: any) => d.metrics as EpochMetrics);
      setComparisonData(runId, epochs);
    },
    [setComparisonData]
  );

  return { comparisonRuns, loadRun, clearComparison };
}
