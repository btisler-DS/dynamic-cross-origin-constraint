import { create } from 'zustand';
import type { EpochMetrics } from '../types/metrics';

interface MetricsState {
  epochs: EpochMetrics[];
  latestEpoch: EpochMetrics | null;
  comparisonRuns: Record<number, EpochMetrics[]>;
  addEpoch: (epoch: EpochMetrics) => void;
  setEpochs: (epochs: EpochMetrics[]) => void;
  clearEpochs: () => void;
  setComparisonData: (runId: number, epochs: EpochMetrics[]) => void;
  clearComparison: () => void;
}

export const useMetricsStore = create<MetricsState>((set) => ({
  epochs: [],
  latestEpoch: null,
  comparisonRuns: {},
  addEpoch: (epoch) =>
    set((state) => ({
      epochs: [...state.epochs, epoch],
      latestEpoch: epoch,
    })),
  setEpochs: (epochs) =>
    set({ epochs, latestEpoch: epochs[epochs.length - 1] ?? null }),
  clearEpochs: () => set({ epochs: [], latestEpoch: null }),
  setComparisonData: (runId, epochs) =>
    set((state) => ({
      comparisonRuns: { ...state.comparisonRuns, [runId]: epochs },
    })),
  clearComparison: () => set({ comparisonRuns: {} }),
}));
