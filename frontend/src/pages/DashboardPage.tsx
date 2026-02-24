import { useSimulation } from '../hooks/useSimulation';
import { useMetricsStream } from '../hooks/useMetricsStream';
import { useMetricsStore } from '../store/metricsSlice';
import RunControlPanel from '../components/dashboard/RunControlPanel';
import ParameterForm from '../components/dashboard/ParameterForm';
import LiveMetricsPanel from '../components/dashboard/LiveMetricsPanel';
import GridVisualization from '../components/dashboard/GridVisualization';
import EntropyChart from '../components/charts/EntropyChart';
import MutualInfoChart from '../components/charts/MutualInfoChart';
import TransferEntropyChart from '../components/charts/TransferEntropyChart';
import SurvivalChart from '../components/charts/SurvivalChart';
import EnergyROIChart from '../components/charts/EnergyROIChart';
import ZipfChart from '../components/charts/ZipfChart';
import SignalHeatmap from '../components/charts/SignalHeatmap';
import KillSwitchButton from '../components/interventions/KillSwitchButton';
import PerturbationControls from '../components/interventions/PerturbationControls';

export default function DashboardPage() {
  const { activeRun } = useSimulation();
  const epochs = useMetricsStore((s) => s.epochs);

  useMetricsStream(activeRun?.id ?? null);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <RunControlPanel />
          <KillSwitchButton />
          <PerturbationControls />
          <ParameterForm />
        </div>
        <div className="lg:col-span-3 space-y-6">
          <LiveMetricsPanel />
          <GridVisualization />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <EntropyChart data={epochs} />
            <MutualInfoChart data={epochs} />
            <TransferEntropyChart data={epochs} />
            <SurvivalChart data={epochs} />
            <EnergyROIChart data={epochs} />
            <ZipfChart data={epochs} />
          </div>
          <SignalHeatmap data={epochs} />
        </div>
      </div>
    </div>
  );
}
