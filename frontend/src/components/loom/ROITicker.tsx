/**
 * ROITicker — Recharts LineChart showing Protocol 1 inquiry ROI over epochs
 * vs. a flat Protocol 0 baseline reference line.
 *
 * Protocol 0 reference ROI comes from Run 10: ~0.001328.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { LoomEpoch } from '../../api/loom';

interface Props {
  epochs: LoomEpoch[];
  currentEpoch: number;
  protocol?: number;
}

const P0_BASELINE_ROI = 0.001328; // Run 10 average ROI

export default function ROITicker({ epochs, currentEpoch, protocol = 1 }: Props) {
  const isP0 = protocol === 0;
  const data = epochs
    .filter((e) => e.epoch <= currentEpoch)
    .map((e) => ({
      epoch: e.epoch,
      roi: e.inquiry_roi ?? e.energy_roi,
    }));

  return (
    <div className="flex flex-col h-full">
      <span className="text-xs text-gray-400 uppercase tracking-wide mb-2">
        Metabolic ROI
      </span>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="epoch"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            label={{ value: 'Epoch', position: 'insideBottom', offset: -2, fill: '#6b7280', fontSize: 10 }}
          />
          <YAxis
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            tickFormatter={(v: number) => v.toFixed(4)}
            width={56}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', fontSize: 11 }}
            formatter={(v: number) => [v?.toFixed(6), 'ROI']}
          />
          <Legend wrapperStyle={{ fontSize: 10, color: '#9ca3af' }} />
          {!isP0 && (
            <ReferenceLine
              y={P0_BASELINE_ROI}
              stroke="#6b7280"
              strokeDasharray="4 2"
              label={{ value: 'P0 baseline', position: 'right', fill: '#6b7280', fontSize: 9 }}
            />
          )}
          <Line
            type="monotone"
            dataKey="roi"
            name={isP0 ? 'Energy ROI' : 'Inquiry ROI'}
            stroke={isP0 ? '#a3a3a3' : '#60a5fa'}
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
