import { useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useRunComparison } from '../../hooks/useRunComparison';

const RUN_COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'];

interface Props {
  runIds: number[];
}

export default function ComparisonView({ runIds }: Props) {
  const { comparisonRuns, loadRun } = useRunComparison();

  useEffect(() => {
    runIds.forEach((id) => {
      if (!comparisonRuns[id]) loadRun(id);
    });
  }, [runIds, comparisonRuns, loadRun]);

  // Build overlay data (aligned by epoch)
  const maxEpochs = Math.max(...runIds.map((id) => comparisonRuns[id]?.length ?? 0));
  const survivalData = Array.from({ length: maxEpochs }, (_, i) => {
    const point: Record<string, number> = { epoch: i };
    runIds.forEach((id) => {
      const epochs = comparisonRuns[id];
      if (epochs?.[i]) {
        point[`Run #${id}`] = epochs[i].survival_rate;
      }
    });
    return point;
  });

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <h3 className="text-sm font-semibold mb-2 text-gray-400">Survival Rate Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={survivalData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="epoch" stroke="#666" />
            <YAxis stroke="#666" domain={[0, 1]} />
            <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }} />
            <Legend />
            {runIds.map((id, i) => (
              <Line
                key={id}
                type="monotone"
                dataKey={`Run #${id}`}
                stroke={RUN_COLORS[i % RUN_COLORS.length]}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
