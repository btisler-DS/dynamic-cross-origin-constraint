import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { EpochMetrics } from '../../types/metrics';

interface Props { data: EpochMetrics[]; }

export default function EnergyROIChart({ data }: Props) {
  const chartData = data.map((d) => ({
    epoch: d.epoch,
    roi: d.energy_roi ?? 0,
  }));

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Energy ROI (Success / Joule)</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="epoch" stroke="#666" tick={{ fontSize: 11 }} />
          <YAxis stroke="#666" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
          <Line type="monotone" dataKey="roi" stroke="#1abc9c" name="Energy ROI" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
