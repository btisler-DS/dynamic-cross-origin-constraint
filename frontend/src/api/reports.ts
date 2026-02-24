import client from './client';

export async function downloadJsonReport(runId: number) {
  const { data } = await client.get(`/runs/${runId}/report/json`);
  return data;
}

export async function downloadPdfReport(runId: number) {
  const response = await client.get(`/runs/${runId}/report/pdf`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement('a');
  a.href = url;
  a.download = `run_${runId}_report.pdf`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export async function downloadWeights(runId: number) {
  const response = await client.get(`/runs/${runId}/weights`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const a = document.createElement('a');
  a.href = url;
  a.download = `run_${runId}_weights.pt`;
  a.click();
  window.URL.revokeObjectURL(url);
}
