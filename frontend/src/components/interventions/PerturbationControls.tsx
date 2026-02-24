import { useSimulationStore } from '../../store/simulationSlice';
import { triggerIntervention } from '../../api/interventions';

export default function PerturbationControls() {
  const activeRun = useSimulationStore((s) => s.activeRun);

  const isRunning = activeRun?.status === 'running';

  const perturbations = [
    { type: 'double_metabolic_cost', label: 'Double Metabolic Cost' },
    { type: 'flip_axes', label: 'Flip Axes' },
    { type: 'signal_noise', label: 'Add Signal Noise' },
  ];

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Perturbations</h3>
      <div className="space-y-1">
        {perturbations.map(({ type, label }) => (
          <button
            key={type}
            disabled={!isRunning}
            onClick={() => activeRun && triggerIntervention(activeRun.id, type)}
            className={`w-full text-left px-3 py-1.5 text-sm rounded border ${
              isRunning
                ? 'bg-gray-800 hover:bg-gray-700 border-gray-700 text-gray-300'
                : 'bg-gray-900 border-gray-800 text-gray-600 cursor-not-allowed'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {!isRunning && (
        <p className="text-[10px] text-gray-600 mt-2">Start a run to enable perturbations</p>
      )}
    </div>
  );
}
