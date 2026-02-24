import client from './client';
import type { Run, RunConfig } from '../types/run';
import type { HashChainEntry, HashChainVerifyResult } from '../types/metrics';

export async function createRun(config: RunConfig): Promise<Run> {
  const { data } = await client.post('/runs', config);
  return data;
}

export async function listRuns(skip = 0, limit = 50): Promise<{ runs: Run[]; total: number }> {
  const { data } = await client.get('/runs', { params: { skip, limit } });
  return data;
}

export async function getRun(id: number): Promise<Run> {
  const { data } = await client.get(`/runs/${id}`);
  return data;
}

export async function deleteRun(id: number): Promise<void> {
  await client.delete(`/runs/${id}`);
}

export async function stopRun(id: number): Promise<void> {
  await client.post(`/runs/${id}/stop`);
}

export async function pauseRun(id: number): Promise<void> {
  await client.post(`/runs/${id}/pause`);
}

export async function resumeRun(id: number): Promise<void> {
  await client.post(`/runs/${id}/resume`);
}

export async function getEpochs(id: number): Promise<unknown[]> {
  const { data } = await client.get(`/runs/${id}/epochs`);
  return data;
}

export async function getHashChain(id: number): Promise<HashChainEntry[]> {
  const { data } = await client.get(`/runs/${id}/hash-chain`);
  return data;
}

export async function verifyHashChain(id: number): Promise<HashChainVerifyResult> {
  const { data } = await client.post(`/runs/${id}/hash-chain/verify`);
  return data;
}
