import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { EpochMetrics } from '../../types/metrics';

interface Props { data: EpochMetrics[]; }

export default function EntropyChart({ data }: Props) {
  const chartData = data.map((d) => ({
    epoch: d.epoch,
    A: d.entropy?.A ?? 0,
    B: d.entropy?.B ?? 0,
    C: d.entropy?.C ?? 0,
  }));

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Shannon Entropy</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="epoch" stroke="#666" tick={{ fontSize: 11 }} />
          <YAxis stroke="#666" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Line type="monotone" dataKey="A" stroke="#3498db" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="B" stroke="#e67e22" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="C" stroke="#9b59b6" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
