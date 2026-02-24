import { useEffect, useState } from 'react';
import client from '../api/client';
import type { Preset } from '../types/config';
import { useSimulationStore } from '../store/simulationSlice';

export default function SettingsPage() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const { setConfig } = useSimulationStore();

  useEffect(() => {
    client.get('/presets').then((r) => setPresets(r.data)).catch(() => {});
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Settings</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {presets.map((preset) => (
          <div key={preset.name} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-lg font-semibold mb-1">{preset.name}</h3>
            <p className="text-sm text-gray-400 mb-3">{preset.description}</p>
            <ul className="text-xs text-gray-500 mb-3 space-y-0.5">
              {preset.constraints.map((c, i) => (
                <li key={i}>- {c}</li>
              ))}
            </ul>
            <button
              onClick={() => setConfig({ ...preset.config, preset_name: preset.name } as any)}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm"
            >
              Apply Preset
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
