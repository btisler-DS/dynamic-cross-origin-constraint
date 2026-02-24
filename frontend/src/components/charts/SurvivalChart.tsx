import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { EpochMetrics } from '../../types/metrics';

interface Props { data: EpochMetrics[]; }

export default function SurvivalChart({ data }: Props) {
  const chartData = data.map((d) => ({
    epoch: d.epoch,
    survival: d.survival_rate,
    target: d.target_reached_rate,
  }));

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Survival & Target Rate</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="epoch" stroke="#666" tick={{ fontSize: 11 }} />
          <YAxis stroke="#666" tick={{ fontSize: 11 }} domain={[0, 1]} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
          <Line type="monotone" dataKey="survival" stroke="#2ecc71" name="Survival" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="target" stroke="#f39c12" name="Target" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
