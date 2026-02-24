import { downloadPdfReport, downloadWeights } from '../../api/reports';

interface Props { runId: number; }

export default function DownloadButtons({ runId }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => downloadPdfReport(runId)}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm"
      >
        Download PDF
      </button>
      <button
        onClick={() => {
          const a = document.createElement('a');
          a.href = `/api/runs/${runId}/report/json`;
          a.download = `run_${runId}_report.json`;
          a.click();
        }}
        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
      >
        Download JSON
      </button>
      <button
        onClick={() => {
          const a = document.createElement('a');
          a.href = `/api/runs/${runId}/report/md`;
          a.download = `run_${runId}_report.md`;
          a.click();
        }}
        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
      >
        Download Markdown
      </button>
      <button
        onClick={() => downloadWeights(runId)}
        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm"
      >
        Download Weights (.pt)
      </button>
    </div>
  );
}
