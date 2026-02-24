import client from './client';
import type { LoomEpoch } from './loom';

export interface RunConfig {
  epochs: number;
  episodes: number;
  seed: number;
  protocol: number;
}

export type RunStatus = 'idle' | 'running' | 'completed' | 'stopped' | 'failed';

export interface LiveStatus {
  status: RunStatus;
  protocol: number;
  current_epoch: number;
  total_epochs: number;
  epochs: LoomEpoch[];
  crystallization_epoch: number | null;
  error: string | null;
  run_id: number | null;
}

export async function startRun(
  config: RunConfig,
): Promise<{ ok: boolean; error?: string }> {
  const { data } = await client.post<{ ok: boolean; error?: string }>(
    '/control/start',
    config,
  );
  return data;
}

export async function stopRun(): Promise<void> {
  await client.post('/control/stop');
}

export async function fetchLiveStatus(): Promise<LiveStatus> {
  const { data } = await client.get<LiveStatus>('/control/live');
  return data;
}
