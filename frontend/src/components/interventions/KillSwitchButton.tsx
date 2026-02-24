import { useState } from 'react';
import { useSimulationStore } from '../../store/simulationSlice';
import { triggerIntervention } from '../../api/interventions';

export default function KillSwitchButton() {
  const activeRun = useSimulationStore((s) => s.activeRun);
  const [killed, setKilled] = useState(false);

  const isRunning = activeRun?.status === 'running';

  const toggle = async () => {
    if (!activeRun || !isRunning) return;
    const type = killed ? 'restore_comm' : 'kill_switch';
    await triggerIntervention(activeRun.id, type);
    setKilled(!killed);
  };

  return (
    <button
      onClick={toggle}
      disabled={!isRunning}
      className={`w-full px-4 py-2 rounded text-sm font-medium transition-colors ${
        !isRunning
          ? 'bg-gray-800 text-gray-500 border border-gray-700 cursor-not-allowed'
          : killed
            ? 'bg-green-700 hover:bg-green-600 text-white'
            : 'bg-red-700 hover:bg-red-600 text-white'
      }`}
    >
      {killed ? 'Restore Communication' : 'Kill Communication'}
      {!isRunning && <span className="block text-[10px] text-gray-600 mt-0.5">Requires active run</span>}
    </button>
  );
}
