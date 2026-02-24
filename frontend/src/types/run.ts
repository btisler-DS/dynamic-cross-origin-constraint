export interface RunConfig {
  seed: number;
  num_epochs: number;
  episodes_per_epoch: number;
  grid_size: number;
  num_obstacles: number;
  z_layers: number;
  max_steps: number;
  energy_budget: number;
  move_cost: number;
  collision_penalty: number;
  signal_dim: number;
  hidden_dim: number;
  learning_rate: number;
  gamma: number;
  communication_tax_rate: number;
  survival_bonus: number;
  preset_name?: string;
}

export interface Run {
  id: number;
  seed: number;
  status: string;
  preset_name: string | null;
  current_epoch: number;
  total_epochs: number;
  final_hash: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  params?: RunConfig;
}
