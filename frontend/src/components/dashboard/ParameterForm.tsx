import { useEffect, useState } from 'react';
import { useSimulationStore } from '../../store/simulationSlice';
import type { Preset } from '../../types/config';
import client from '../../api/client';

const PARAM_FIELDS = [
  { key: 'seed', label: 'Seed', type: 'number' },
  { key: 'num_epochs', label: 'Epochs', type: 'number' },
  { key: 'episodes_per_epoch', label: 'Episodes/Epoch', type: 'number' },
  { key: 'grid_size', label: 'Grid Size', type: 'number' },
  { key: 'num_obstacles', label: 'Obstacles', type: 'number' },
  { key: 'max_steps', label: 'Max Steps', type: 'number' },
  { key: 'energy_budget', label: 'Energy Budget', type: 'number', step: 1 },
  { key: 'move_cost', label: 'Move Cost', type: 'number', step: 0.1 },
  { key: 'collision_penalty', label: 'Collision Penalty', type: 'number', step: 0.5 },
  { key: 'communication_tax_rate', label: 'Comm Tax Rate', type: 'number', step: 0.001 },
  { key: 'learning_rate', label: 'Learning Rate', type: 'number', step: 0.0001 },
  { key: 'gamma', label: 'Gamma', type: 'number', step: 0.01 },
  { key: 'survival_bonus', label: 'Survival Bonus', type: 'number', step: 0.01 },
] as const;

export default function ParameterForm() {
  const { config, setConfig } = useSimulationStore();
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => {
    client.get('/presets').then((r) => setPresets(r.data)).catch(() => {});
  }, []);

  const applyPreset = (preset: Preset) => {
    setConfig({ ...preset.config, preset_name: preset.name });
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 max-h-[600px] overflow-y-auto">
      <h2 className="text-lg font-semibold mb-3">Parameters</h2>

      {presets.length > 0 && (
        <div className="mb-4">
          <label className="block text-xs text-gray-400 mb-1">Presets</label>
          <div className="flex flex-wrap gap-1">
            {presets.map((p) => (
              <button
                key={p.name}
                onClick={() => applyPreset(p)}
                className="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded border border-gray-700"
                title={p.description}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        {PARAM_FIELDS.map(({ key, label, type, step }) => (
          <div key={key}>
            <label className="block text-xs text-gray-400 mb-0.5">{label}</label>
            <input
              type={type}
              step={step}
              value={(config as any)[key]}
              onChange={(e) =>
                setConfig({ [key]: type === 'number' ? Number(e.target.value) : e.target.value })
              }
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
