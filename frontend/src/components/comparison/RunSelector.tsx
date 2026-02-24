import { useEffect, useState } from 'react';
import { listRuns } from '../../api/runs';
import type { Run } from '../../types/run';

interface Props {
  selected: number[];
  onChange: (ids: number[]) => void;
}

export default function RunSelector({ selected, onChange }: Props) {
  const [runs, setRuns] = useState<Run[]>([]);

  useEffect(() => {
    listRuns().then((r) => setRuns(r.runs.filter((run) => run.status === 'completed')));
  }, []);

  const toggle = (id: number) => {
    if (selected.includes(id)) {
      onChange(selected.filter((r) => r !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 mb-4">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">Select runs to compare</h3>
      <div className="flex flex-wrap gap-2">
        {runs.map((run) => (
          <button
            key={run.id}
            onClick={() => toggle(run.id)}
            className={`px-3 py-1.5 rounded text-sm border ${
              selected.includes(run.id)
                ? 'bg-blue-600 border-blue-500 text-white'
                : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700'
            }`}
          >
            Run #{run.id} (seed {run.seed})
          </button>
        ))}
        {runs.length === 0 && <p className="text-gray-500 text-sm">No completed runs available</p>}
      </div>
    </div>
  );
}
