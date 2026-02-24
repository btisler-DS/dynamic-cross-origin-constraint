import { useEffect, useState } from 'react';
import { downloadJsonReport } from '../../api/reports';

interface Props { runId: number; }

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-gray-800 rounded-lg p-3">
      <h4 className="text-sm font-semibold text-blue-400 mb-2">{title}</h4>
      {children}
    </div>
  );
}

export default function ReportPreview({ runId }: Props) {
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    downloadJsonReport(runId).then(setReport).catch(() => setReport(null));
  }, [runId]);

  if (!report) return <div className="text-gray-500 text-sm mt-4">Loading report...</div>;

  const analysis = report.analysis ?? {};
  const phase = analysis.phase_transition ?? {};
  const te = analysis.isomorphism_bridge ?? {};
  const zipf = analysis.zipf_validation ?? {};
  const perturb = analysis.perturbation_resilience ?? {};

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 mt-4 space-y-4">
      <div className="border-b border-gray-800 pb-3">
        <p className="text-xs italic text-blue-300 mb-2">"{report.thesis}"</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><span className="text-gray-400">Run:</span> #{report.run?.id}</div>
          <div><span className="text-gray-400">Seed:</span> {report.run?.seed}</div>
          <div><span className="text-gray-400">Epochs:</span> {report.summary?.total_epochs}</div>
          <div><span className="text-gray-400">Status:</span> {report.run?.status}</div>
          <div><span className="text-gray-400">Survival:</span> {(report.summary?.final_survival_rate * 100)?.toFixed(1)}%</div>
          <div><span className="text-gray-400">Target:</span> {(report.summary?.final_target_rate * 100)?.toFixed(1)}%</div>
          <div><span className="text-gray-400">Energy ROI:</span> {report.summary?.mean_energy_roi?.toFixed(6)}</div>
          <div><span className="text-gray-400">Hash:</span> <span className="font-mono text-[10px]">{report.run?.final_hash?.slice(0, 16)}...</span></div>
        </div>
      </div>

      <Section title="1. Phase Transition — Entropy Cliff">
        <p className="text-sm text-gray-300 mb-2">{phase.narrative}</p>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="bg-gray-800 rounded p-2">
            <span className="text-gray-500">Cliff Epoch</span>
            <p className="font-mono text-lg">{(phase.cliff_epoch ?? 0) + 1}</p>
          </div>
          <div className="bg-gray-800 rounded p-2">
            <span className="text-gray-500">Entropy Drop</span>
            <p className="font-mono text-lg">{phase.cliff_magnitude?.toFixed(3)}</p>
          </div>
          <div className="bg-gray-800 rounded p-2">
            <span className="text-gray-500">Confirmed</span>
            <p className={`font-mono text-lg ${phase.phase_confirmed ? 'text-green-400' : 'text-yellow-400'}`}>
              {phase.phase_confirmed ? 'Yes' : 'No'}
            </p>
          </div>
        </div>
      </Section>

      <Section title="2. Isomorphism Bridge — Agent C as Weaver">
        <p className="text-sm text-gray-300 mb-2 whitespace-pre-line">{te.narrative}</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-800 rounded p-2">
            <span className="text-gray-500">C Receives</span>
            <p className="font-mono">{te.c_receives_total?.toFixed(5)}</p>
          </div>
          <div className="bg-gray-800 rounded p-2">
            <span className="text-gray-500">C Sends</span>
            <p className="font-mono">{te.c_sends_total?.toFixed(5)}</p>
          </div>
          <div className="bg-gray-800 rounded p-2 col-span-2">
            <span className="text-gray-500">B→C vs A→C Asymmetry</span>
            <p className="font-mono">{te.asymmetry_b_over_a?.toFixed(5)}</p>
          </div>
        </div>
      </Section>

      <Section title="3. Zipf's Law — Linguistic Efficiency">
        <p className="text-sm text-gray-300 mb-2">{zipf.narrative}</p>
        <div className="grid grid-cols-3 gap-2 text-xs">
          {Object.entries(zipf.agents ?? {}).map(([agent, vals]: [string, any]) => (
            <div key={agent} className="bg-gray-800 rounded p-2">
              <span className="text-gray-500">Agent {agent}</span>
              <p className="font-mono">α={vals?.alpha?.toFixed(2)} R²={vals?.r_squared?.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="4. Perturbation Resilience">
        <p className="text-sm text-gray-300">{perturb.narrative}</p>
      </Section>
    </div>
  );
}
