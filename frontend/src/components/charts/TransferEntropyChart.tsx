import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { EpochMetrics } from '../../types/metrics';

interface Props { data: EpochMetrics[]; }

const TE_COLORS: Record<string, string> = {
  'A→B': '#3498db', 'A→C': '#2980b9',
  'B→A': '#e67e22', 'B→C': '#d35400',
  'C→A': '#9b59b6', 'C→B': '#8e44ad',
};

export default function TransferEntropyChart({ data }: Props) {
  const chartData = data.map((d) => {
    const te = d.transfer_entropy ?? {};
    return { epoch: d.epoch, ...te };
  });

  const keys = Object.keys(data[0]?.transfer_entropy ?? {});

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Transfer Entropy (6 directed pairs)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="epoch" stroke="#666" tick={{ fontSize: 11 }} />
          <YAxis stroke="#666" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          {keys.map((k) => (
            <Line key={k} type="monotone" dataKey={k} stroke={TE_COLORS[k] ?? '#999'} dot={false} strokeWidth={1.5} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
