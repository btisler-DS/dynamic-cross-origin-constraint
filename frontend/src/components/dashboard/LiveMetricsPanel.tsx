import { useMetricsStore } from '../../store/metricsSlice';

export default function LiveMetricsPanel() {
  const latest = useMetricsStore((s) => s.latestEpoch);

  if (!latest) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 text-gray-500 text-sm">
        No data yet. Start a run to see live metrics.
      </div>
    );
  }

  const cards = [
    { label: 'Epoch', value: latest.epoch + 1 },
    { label: 'Survival', value: `${(latest.survival_rate * 100).toFixed(1)}%` },
    { label: 'Target Hit', value: `${(latest.target_reached_rate * 100).toFixed(1)}%` },
    { label: 'Avg Steps', value: latest.avg_steps.toFixed(1) },
    { label: 'Energy ROI', value: latest.energy_roi?.toFixed(5) ?? 'N/A' },
    { label: 'Comm', value: latest.comm_killed ? 'KILLED' : 'Active' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map(({ label, value }) => (
        <div key={label} className="bg-gray-900 rounded-lg p-3 border border-gray-800">
          <p className="text-xs text-gray-400">{label}</p>
          <p className="text-lg font-mono font-semibold">{value}</p>
        </div>
      ))}
    </div>
  );
}
