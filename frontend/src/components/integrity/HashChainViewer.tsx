import { useEffect, useState } from 'react';
import { getHashChain, verifyHashChain } from '../../api/runs';
import type { HashChainEntry, HashChainVerifyResult } from '../../types/metrics';

interface Props { runId: number; }

export default function HashChainViewer({ runId }: Props) {
  const [chain, setChain] = useState<HashChainEntry[]>([]);
  const [verification, setVerification] = useState<HashChainVerifyResult | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  useEffect(() => {
    getHashChain(runId).then(setChain);
  }, [runId]);

  const handleVerify = async () => {
    const result = await verifyHashChain(runId);
    setVerification(result);
  };

  const toggleExpand = (epoch: number) => {
    const next = new Set(expanded);
    if (next.has(epoch)) next.delete(epoch);
    else next.add(epoch);
    setExpanded(next);
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-400">Hash Chain ({chain.length} entries)</h3>
        <button onClick={handleVerify} className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs">
          Verify Chain
        </button>
      </div>

      {verification && (
        <div className={`mb-3 px-3 py-2 rounded text-sm ${
          verification.valid ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'
        }`}>
          {verification.message}
        </div>
      )}

      <div className="space-y-1 max-h-[400px] overflow-y-auto">
        {chain.map((entry) => (
          <div key={entry.epoch} className="border border-gray-800 rounded">
            <button
              onClick={() => toggleExpand(entry.epoch)}
              className="w-full text-left px-3 py-2 text-xs hover:bg-gray-800 flex justify-between"
            >
              <span>Epoch {entry.epoch}</span>
              <span className="font-mono text-gray-500">{entry.hash.slice(0, 16)}...</span>
            </button>
            {expanded.has(entry.epoch) && (
              <div className="px-3 py-2 text-xs border-t border-gray-800 bg-gray-800/30 space-y-1">
                <p><span className="text-gray-400">Hash:</span> <span className="font-mono break-all">{entry.hash}</span></p>
                <p><span className="text-gray-400">Prev:</span> <span className="font-mono break-all">{entry.prev_hash}</span></p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
