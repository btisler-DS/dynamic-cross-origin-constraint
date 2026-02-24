import { useState } from 'react';
import RunSelector from '../components/comparison/RunSelector';
import ComparisonView from '../components/comparison/ComparisonView';

export default function ComparisonPage() {
  const [selectedRuns, setSelectedRuns] = useState<number[]>([]);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Run Comparison</h2>
      <RunSelector selected={selectedRuns} onChange={setSelectedRuns} />
      {selectedRuns.length >= 2 && <ComparisonView runIds={selectedRuns} />}
    </div>
  );
}
