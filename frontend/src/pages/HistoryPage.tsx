import { useEffect, useState } from 'react';
import { listRuns, deleteRun } from '../api/runs';
import type { Run } from '../types/run';

export default function HistoryPage() {
  const [runs, setRuns] = useState<Run[]>([]);

  useEffect(() => {
    listRuns().then((r) => setRuns(r.runs));
  }, []);

  const handleDelete = async (id: number) => {
    await deleteRun(id);
    setRuns((prev) => prev.filter((r) => r.id !== id));
  };

  const statusColor = (s: string) => {
    switch (s) {
      case 'running': return 'text-green-400';
      case 'completed': return 'text-blue-400';
      case 'failed': return 'text-red-400';
      case 'paused': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Run History</h2>
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-800">
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Seed</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Epochs</th>
              <th className="px-4 py-2 text-left">Preset</th>
              <th className="px-4 py-2 text-left">Created</th>
              <th className="px-4 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                <td className="px-4 py-2 font-mono">{run.id}</td>
                <td className="px-4 py-2 font-mono">{run.seed}</td>
                <td className={`px-4 py-2 font-medium ${statusColor(run.status)}`}>{run.status}</td>
                <td className="px-4 py-2">{run.current_epoch}/{run.total_epochs}</td>
                <td className="px-4 py-2">{run.preset_name ?? '-'}</td>
                <td className="px-4 py-2 text-gray-400">{new Date(run.created_at).toLocaleString()}</td>
                <td className="px-4 py-2">
                  <button
                    onClick={() => handleDelete(run.id)}
                    className="text-red-400 hover:text-red-300 text-xs"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {runs.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No runs yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
