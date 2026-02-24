import { create } from 'zustand';
import type { Run, RunConfig } from '../types/run';

interface SimulationState {
  activeRun: Run | null;
  config: RunConfig;
  runs: Run[];
  setActiveRun: (run: Run | null) => void;
  setConfig: (config: Partial<RunConfig>) => void;
  setRuns: (runs: Run[]) => void;
  updateRunStatus: (id: number, status: string) => void;
  updateRunEpoch: (id: number, epoch: number) => void;
}

const DEFAULT_CONFIG: RunConfig = {
  seed: 42,
  num_epochs: 100,
  episodes_per_epoch: 10,
  grid_size: 20,
  num_obstacles: 8,
  z_layers: 8,
  max_steps: 100,
  energy_budget: 100.0,
  move_cost: 1.0,
  collision_penalty: 5.0,
  signal_dim: 8,
  hidden_dim: 64,
  learning_rate: 0.001,
  gamma: 0.99,
  communication_tax_rate: 0.01,
  survival_bonus: 0.1,
};

export const useSimulationStore = create<SimulationState>((set) => ({
  activeRun: null,
  config: DEFAULT_CONFIG,
  runs: [],
  setActiveRun: (run) => set({ activeRun: run }),
  setConfig: (partial) =>
    set((state) => ({ config: { ...state.config, ...partial } })),
  setRuns: (runs) => set({ runs }),
  updateRunStatus: (id, status) =>
    set((state) => ({
      runs: state.runs.map((r) => (r.id === id ? { ...r, status } : r)),
      activeRun:
        state.activeRun?.id === id
          ? { ...state.activeRun, status }
          : state.activeRun,
    })),
  updateRunEpoch: (id, epoch) =>
    set((state) => ({
      activeRun:
        state.activeRun?.id === id
          ? { ...state.activeRun, current_epoch: epoch + 1 }
          : state.activeRun,
    })),
}));
