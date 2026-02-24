import client from './client';

export async function triggerIntervention(
  runId: number,
  interventionType: string,
  params: Record<string, unknown> = {}
) {
  const { data } = await client.post(`/runs/${runId}/interventions`, {
    intervention_type: interventionType,
    params,
  });
  return data;
}
