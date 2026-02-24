import { useRef, useEffect } from 'react';
import type { EpochMetrics } from '../../types/metrics';

interface Props {
  data: EpochMetrics[];
}

// Scientific viridis-inspired colormap (dark purple → teal → yellow)
function viridis(t: number): [number, number, number] {
  t = Math.max(0, Math.min(1, t));
  // Simplified viridis: purple(0) → blue(0.25) → teal(0.5) → green(0.75) → yellow(1)
  if (t < 0.25) {
    const s = t / 0.25;
    return [
      Math.round(68 + s * (-4)),
      Math.round(1 + s * 40),
      Math.round(84 + s * 50),
    ];
  } else if (t < 0.5) {
    const s = (t - 0.25) / 0.25;
    return [
      Math.round(64 - s * 30),
      Math.round(41 + s * 80),
      Math.round(134 - s * 10),
    ];
  } else if (t < 0.75) {
    const s = (t - 0.5) / 0.25;
    return [
      Math.round(34 + s * 80),
      Math.round(121 + s * 60),
      Math.round(124 - s * 60),
    ];
  } else {
    const s = (t - 0.75) / 0.25;
    return [
      Math.round(114 + s * 139),
      Math.round(181 + s * 48),
      Math.round(64 - s * 40),
    ];
  }
}

const AGENT_LABELS = ['Agent A (RNN)', 'Agent B (CNN)', 'Agent C (GNN)'];
const AGENT_KEYS = ['A', 'B', 'C'];
const ROW_HEIGHT = 40;
const LABEL_WIDTH = 130;
const SCALE_HEIGHT = 20;
const MARGIN_TOP = 10;
const MARGIN_BOTTOM = 40;

export default function SignalHeatmap({ data }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const numEpochs = data.length;
    const heatW = canvas.width - LABEL_WIDTH - 20;
    const cellW = Math.max(1, heatW / numEpochs);
    const totalH = MARGIN_TOP + ROW_HEIGHT * 3 + MARGIN_BOTTOM + SCALE_HEIGHT + 10;
    canvas.height = totalH;

    // Find global min/max entropy for normalization
    let globalMin = Infinity;
    let globalMax = -Infinity;
    for (const epoch of data) {
      for (const key of AGENT_KEYS) {
        const v = epoch.entropy?.[key] ?? 0;
        if (v < globalMin) globalMin = v;
        if (v > globalMax) globalMax = v;
      }
    }
    const range = globalMax - globalMin || 1;

    // Background
    ctx.fillStyle = '#111119';
    ctx.fillRect(0, 0, canvas.width, totalH);

    // Draw heatmap rows
    AGENT_KEYS.forEach((key, rowIdx) => {
      const y = MARGIN_TOP + rowIdx * ROW_HEIGHT;

      // Label
      ctx.fillStyle = '#ccc';
      ctx.font = '11px monospace';
      ctx.textBaseline = 'middle';
      ctx.fillText(AGENT_LABELS[rowIdx], 8, y + ROW_HEIGHT / 2);

      // Cells
      data.forEach((epoch, col) => {
        const v = epoch.entropy?.[key] ?? 0;
        const t = (v - globalMin) / range;
        const [r, g, b] = viridis(t);
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        const x = LABEL_WIDTH + col * cellW;
        ctx.fillRect(x, y + 2, cellW + 0.5, ROW_HEIGHT - 4);
      });

      // Row border
      ctx.strokeStyle = '#333';
      ctx.lineWidth = 0.5;
      ctx.strokeRect(LABEL_WIDTH, y + 2, heatW, ROW_HEIGHT - 4);
    });

    // Epoch axis labels
    const axisY = MARGIN_TOP + ROW_HEIGHT * 3 + 4;
    ctx.fillStyle = '#777';
    ctx.font = '9px monospace';
    ctx.textBaseline = 'top';
    ctx.textAlign = 'center';
    const labelInterval = Math.max(1, Math.floor(numEpochs / 10));
    for (let i = 0; i < numEpochs; i += labelInterval) {
      const x = LABEL_WIDTH + (i + 0.5) * cellW;
      ctx.fillText(String(i + 1), x, axisY);
    }
    // Last epoch
    ctx.fillText(String(numEpochs), LABEL_WIDTH + (numEpochs - 0.5) * cellW, axisY);
    ctx.textAlign = 'start';

    // Epoch label
    ctx.fillStyle = '#888';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Epoch', LABEL_WIDTH + heatW / 2, axisY + 14);
    ctx.textAlign = 'start';

    // Color scale bar
    const scaleY = axisY + 30;
    const scaleW = heatW * 0.6;
    const scaleX = LABEL_WIDTH + (heatW - scaleW) / 2;

    for (let i = 0; i < scaleW; i++) {
      const t = i / scaleW;
      const [r, g, b] = viridis(t);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(scaleX + i, scaleY, 1, SCALE_HEIGHT);
    }
    ctx.strokeStyle = '#555';
    ctx.strokeRect(scaleX, scaleY, scaleW, SCALE_HEIGHT);

    // Scale labels
    ctx.fillStyle = '#aaa';
    ctx.font = '10px monospace';
    ctx.textBaseline = 'top';
    ctx.textAlign = 'center';
    ctx.fillText(`${globalMin.toFixed(2)} bits`, scaleX, scaleY + SCALE_HEIGHT + 3);
    ctx.fillText(`${globalMax.toFixed(2)} bits`, scaleX + scaleW, scaleY + SCALE_HEIGHT + 3);
    ctx.fillText('Shannon Entropy', scaleX + scaleW / 2, scaleY + SCALE_HEIGHT + 3);
    ctx.textAlign = 'start';
    ctx.textBaseline = 'alphabetic';

  }, [data]);

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h3 className="text-sm font-semibold mb-2 text-gray-400">
        Signal Entropy Heatmap — Protocol Evolution
      </h3>
      <canvas
        ref={canvasRef}
        width={900}
        height={220}
        className="w-full rounded"
      />
      <p className="text-xs text-gray-600 mt-1">
        Dark purple = low entropy (structured protocol) | Yellow = high entropy (noise/exploration)
      </p>
    </div>
  );
}
