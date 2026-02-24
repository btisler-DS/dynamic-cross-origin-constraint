export interface Trajectory {
  grid_size: number;
  target: [number, number];
  obstacles: [number, number][];
  steps: {
    A: [number, number];
    B: [number, number];
    C: [number, number];
    energy: Record<string, number>;
  }[];
}

export interface EpochMetrics {
  epoch: number;
  avg_reward: Record<string, number>;
  survival_rate: number;
  target_reached_rate: number;
  avg_steps: number;
  avg_energy_spent: number;
  losses: Record<string, number>;
  entropy: Record<string, number>;
  mutual_information: Record<string, number>;
  transfer_entropy?: Record<string, number>;
  zipf?: Record<string, ZipfResult>;
  energy_roi?: number;
  comm_killed: boolean;
  interventions?: Intervention[];
  trajectory?: Trajectory | null;
}

export interface ZipfResult {
  alpha: number;
  ks_statistic: number;
  ks_pvalue: number;
  r_squared: number;
}

export interface Intervention {
  epoch: number;
  type: string;
  params: Record<string, unknown>;
  active: boolean;
}

export interface HashChainEntry {
  epoch: number;
  hash: string;
  prev_hash: string;
  metrics_json: string;
}

export interface HashChainVerifyResult {
  valid: boolean;
  total_epochs: number;
  first_invalid_epoch: number | null;
  message: string;
}
