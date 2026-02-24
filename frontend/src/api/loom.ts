import client from './client';

export interface PCAPoint {
  pc1: number;
  pc2: number;
  type_int: number;
  agent: string;
}

export interface LoomEpoch {
  epoch: number;
  type_entropy: number | null;
  D: number | null;
  Q: number | null;
  R: number | null;
  qrc: number | null;
  inquiry_roi: number | null;
  survival_rate: number | null;
  signal_pca: PCAPoint[] | null;
}

export interface LoomData {
  epochs: LoomEpoch[];
  crystallization_epoch: number | null;
  protocol: number;
}

export async function fetchLoomData(runId: number): Promise<LoomData> {
  const { data } = await client.get<LoomData>(`/runs/${runId}/loom`);
  return data;
}

/** Parse a raw run_XX_report.json into LoomData.
 *
 * Handles two formats:
 *  - Legacy flat: { epoch, type_entropy, D, Q, R, qrc, inquiry_roi, ... }
 *  - New nested:  { epoch, inquiry: { type_entropy, type_distribution, ... }, ... }
 *  - Top-level wrapper: { run: {...}, epochs: [...] }
 */
export function parseLoomFile(jsonText: string): LoomData {
  const raw = JSON.parse(jsonText);

  // Unwrap {run, epochs} wrapper if present
  let list: any[];
  if (Array.isArray(raw)) {
    list = raw;
  } else if (raw.epochs) {
    list = raw.epochs;
  } else {
    list = [];
  }

  const epochs: LoomEpoch[] = list.map((m: any) => {
    // New nested format: m.inquiry exists
    if (m.inquiry && typeof m.inquiry === 'object') {
      const inq = m.inquiry;
      const td = inq.type_distribution ?? {};
      return {
        epoch: m.epoch ?? 0,
        type_entropy: inq.type_entropy ?? null,
        D: td.DECLARE ?? null,
        Q: td.QUERY ?? null,
        R: td.RESPOND ?? null,
        qrc: inq.query_response_coupling ?? null,
        inquiry_roi: inq.inquiry_roi ?? null,
        survival_rate: m.survival_rate ?? null,
        signal_pca: m.signal_pca ?? null,
      };
    }
    // Legacy flat format: fields are directly on epoch
    return {
      epoch: m.epoch ?? 0,
      type_entropy: m.type_entropy ?? null,
      D: m.D ?? null,
      Q: m.Q ?? null,
      R: m.R ?? null,
      qrc: m.qrc ?? null,
      inquiry_roi: m.inquiry_roi ?? null,
      survival_rate: m.survival_rate ?? null,
      signal_pca: m.signal_pca ?? null,
    };
  });

  return {
    epochs,
    crystallization_epoch: detectCrystallizationEpoch(epochs),
    protocol: 1,
  };
}

/** Compute crystallization epoch client-side for file-loaded data. */
function detectCrystallizationEpoch(epochs: LoomEpoch[]): number | null {
  let streakStart: number | null = null;
  let count = 0;
  for (const ep of epochs) {
    const te = ep.type_entropy;
    if (te !== null && te < 0.95) {
      if (count === 0) streakStart = ep.epoch;
      count++;
      if (count >= 5 && streakStart !== null) return streakStart;
    } else {
      count = 0;
      streakStart = null;
    }
  }
  return null;
}
