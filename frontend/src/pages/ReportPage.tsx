import { useEffect, useState } from 'react';
import { listRuns } from '../api/runs';
import ReportPreview from '../components/reports/ReportPreview';
import DownloadButtons from '../components/reports/DownloadButtons';
import type { Run } from '../types/run';

export default function ReportPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    listRuns().then((r) => setRuns(r.runs.filter((run) => run.status === 'completed')));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Reports</h2>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <h3 className="text-sm font-semibold mb-2 text-gray-400">Select Run</h3>
          <div className="space-y-1">
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => setSelectedId(run.id)}
                className={`w-full text-left px-3 py-2 rounded text-sm ${
                  selectedId === run.id ? 'bg-blue-600' : 'bg-gray-800 hover:bg-gray-700'
                }`}
              >
                Run #{run.id} — seed {run.seed}
              </button>
            ))}
            {runs.length === 0 && <p className="text-gray-500 text-sm">No completed runs</p>}
          </div>
        </div>
        <div className="lg:col-span-2">
          {selectedId && (
            <>
              <DownloadButtons runId={selectedId} />
              <ReportPreview runId={selectedId} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
