import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { EpochMetrics } from '../../types/metrics';

interface Props { data: EpochMetrics[]; }

export default function ZipfChart({ data }: Props) {
  const latest = data[data.length - 1];
  if (!latest?.zipf) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <h3 className="text-sm font-semibold mb-2 text-gray-400">Zipf Analysis</h3>
        <p className="text-gray-500 text-sm">No data yet</p>
      </div>
    );
  }

  const chartData = Object.entries(latest.zipf).map(([agent, z]) => ({
    agent,
    alpha: z.alpha,
    r_squared: z.r_squared,
  }));

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Zipf Analysis (latest epoch)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="agent" stroke="#666" tick={{ fontSize: 11 }} />
          <YAxis stroke="#666" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Bar dataKey="alpha" fill="#e74c3c" name="Zipf α" />
          <Bar dataKey="r_squared" fill="#3498db" name="R²" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
