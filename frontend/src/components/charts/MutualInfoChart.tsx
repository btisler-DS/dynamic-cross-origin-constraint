import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { EpochMetrics } from '../../types/metrics';

interface Props { data: EpochMetrics[]; }

export default function MutualInfoChart({ data }: Props) {
  const chartData = data.map((d) => {
    const mi = d.mutual_information ?? {};
    return {
      epoch: d.epoch,
      'A-B': mi['A-B'] ?? 0,
      'A-C': mi['A-C'] ?? 0,
      'B-C': mi['B-C'] ?? 0,
    };
  });

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Mutual Information</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="epoch" stroke="#666" tick={{ fontSize: 11 }} />
          <YAxis stroke="#666" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Line type="monotone" dataKey="A-B" stroke="#2ecc71" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="A-C" stroke="#e74c3c" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="B-C" stroke="#f1c40f" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
