/**
 * TypeDistributionChart — Recharts stacked area chart showing the D/Q/R
 * type fractions over the epochs up to the current scrubber position.
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { LoomEpoch } from '../../api/loom';

interface Props {
  epochs: LoomEpoch[];
  currentEpoch: number;
}

export default function TypeDistributionChart({ epochs, currentEpoch }: Props) {
  const data = epochs
    .filter((e) => e.epoch <= currentEpoch && e.D !== null)
    .map((e) => ({
      epoch: e.epoch,
      D: e.D ?? 0,
      Q: e.Q ?? 0,
      R: e.R ?? 0,
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-500">
        No type distribution data (Protocol 0)
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <span className="text-xs text-gray-400 uppercase tracking-wide mb-2">
        Type Distribution
      </span>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="epoch"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            label={{ value: 'Epoch', position: 'insideBottom', offset: -2, fill: '#6b7280', fontSize: 10 }}
          />
          <YAxis
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            domain={[0, 1]}
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            width={36}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', fontSize: 11 }}
            formatter={(v: number, name: string) => [`${(v * 100).toFixed(1)}%`, name]}
          />
          <Legend wrapperStyle={{ fontSize: 10, color: '#9ca3af' }} />
          <Area
            type="monotone"
            dataKey="D"
            name="DECLARE"
            stackId="1"
            stroke="#9ca3af"
            fill="#4b5563"
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="Q"
            name="QUERY"
            stackId="1"
            stroke="#f59e0b"
            fill="#78350f"
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="R"
            name="RESPOND"
            stackId="1"
            stroke="#60a5fa"
            fill="#1e3a5f"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
