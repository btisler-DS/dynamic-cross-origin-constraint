import { useRef, useEffect, useState, useCallback } from 'react';
import { useMetricsStore } from '../../store/metricsSlice';
import type { Trajectory } from '../../types/metrics';

const COLORS = {
  bg: '#0f0f1a',
  grid: '#1a1a2e',
  gridLine: '#252540',
  obstacle: '#e74c3c',
  target: '#2ecc71',
  targetGlow: 'rgba(46, 204, 113, 0.3)',
  agentA: '#3498db',
  agentB: '#e67e22',
  agentC: '#9b59b6',
  trail: 0.15,
};

const CANVAS_SIZE = 440;

export default function GridVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stepRef = useRef(0);
  const [playing, setPlaying] = useState(false);
  const latestEpoch = useMetricsStore((s) => s.latestEpoch);

  const trajectory: Trajectory | null = latestEpoch?.trajectory ?? null;
  const gridSize = trajectory?.grid_size ?? 20;
  const cellSize = CANVAS_SIZE / gridSize;

  const drawAgent = useCallback((
    ctx: CanvasRenderingContext2D,
    pos: [number, number],
    color: string,
    alpha: number,
    cs: number,
    label?: string
  ) => {
    const [r, c] = pos;
    const cx = (c + 0.5) * cs;
    const cy = (r + 0.5) * cs;
    const radius = cs * 0.35;

    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();

    if (label) {
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(label, cx, cy);
    }
    ctx.globalAlpha = 1;
    ctx.textAlign = 'start';
    ctx.textBaseline = 'alphabetic';
  }, []);

  const drawEnergyBar = useCallback((
    ctx: CanvasRenderingContext2D,
    energy: Record<string, number>,
    w: number
  ) => {
    const barW = 60;
    const barH = 6;
    const x0 = w - barW - 50;
    const agents = [
      { name: 'A', color: COLORS.agentA },
      { name: 'B', color: COLORS.agentB },
      { name: 'C', color: COLORS.agentC },
    ];
    agents.forEach(({ name, color }, i) => {
      const y = 8 + i * 14;
      const frac = Math.max(0, (energy[name] ?? 0) / 100);
      ctx.fillStyle = '#222';
      ctx.fillRect(x0, y, barW, barH);
      ctx.fillStyle = color;
      ctx.fillRect(x0, y, barW * frac, barH);
      ctx.fillStyle = '#aaa';
      ctx.font = '9px monospace';
      ctx.fillText(`${name}: ${Math.round(energy[name] ?? 0)}`, x0 + barW + 4, y + barH - 1);
    });
  }, []);

  const drawFrame = useCallback((
    ctx: CanvasRenderingContext2D,
    traj: Trajectory,
    step: number,
    gs: number,
    cs: number
  ) => {
    const w = CANVAS_SIZE;
    const h = CANVAS_SIZE;

    // Background
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = COLORS.gridLine;
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= gs; i++) {
      ctx.beginPath();
      ctx.moveTo(i * cs, 0);
      ctx.lineTo(i * cs, h);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * cs);
      ctx.lineTo(w, i * cs);
      ctx.stroke();
    }

    // Target (glowing)
    if (traj.target) {
      const [tr, tc] = traj.target;
      ctx.fillStyle = COLORS.targetGlow;
      ctx.beginPath();
      ctx.arc((tc + 0.5) * cs, (tr + 0.5) * cs, cs * 1.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = COLORS.target;
      ctx.fillRect(tc * cs + 2, tr * cs + 2, cs - 4, cs - 4);
    }

    // Obstacles
    if (traj.obstacles) {
      for (const obs of traj.obstacles) {
        const [or_, oc] = obs;
        ctx.fillStyle = COLORS.obstacle;
        ctx.fillRect(oc * cs + 1, or_ * cs + 1, cs - 2, cs - 2);
      }
    }

    // Trails (previous positions with fading opacity)
    const trailLen = Math.min(step, 8);
    for (let t = Math.max(0, step - trailLen); t < step; t++) {
      const s = traj.steps[t];
      if (!s) continue;
      const alpha = ((t - (step - trailLen)) / trailLen) * COLORS.trail;
      drawAgent(ctx, s.A, COLORS.agentA, alpha, cs);
      drawAgent(ctx, s.B, COLORS.agentB, alpha, cs);
      drawAgent(ctx, s.C, COLORS.agentC, alpha, cs);
    }

    // Current agents
    if (step < traj.steps.length) {
      const s = traj.steps[step];
      drawAgent(ctx, s.A, COLORS.agentA, 1.0, cs, 'A');
      drawAgent(ctx, s.B, COLORS.agentB, 1.0, cs, 'B');
      drawAgent(ctx, s.C, COLORS.agentC, 1.0, cs, 'C');
      drawEnergyBar(ctx, s.energy, w);
    }

    // Step counter
    ctx.fillStyle = '#888';
    ctx.font = '11px monospace';
    ctx.fillText(`Step ${step + 1} / ${traj.steps.length}`, 6, h - 6);
  }, [drawAgent, drawEnergyBar]);

  // Draw the latest trajectory's first frame whenever new epoch data arrives
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (trajectory && trajectory.steps && trajectory.steps.length > 0 && !playing) {
      drawFrame(ctx, trajectory, 0, gridSize, cellSize);
    } else if (!trajectory) {
      // Placeholder
      ctx.fillStyle = COLORS.bg;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = COLORS.gridLine;
      ctx.lineWidth = 0.5;
      const defaultGs = 20;
      const defaultCs = CANVAS_SIZE / defaultGs;
      for (let i = 0; i <= defaultGs; i++) {
        ctx.beginPath();
        ctx.moveTo(i * defaultCs, 0);
        ctx.lineTo(i * defaultCs, canvas.height);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i * defaultCs);
        ctx.lineTo(canvas.width, i * defaultCs);
        ctx.stroke();
      }
      ctx.fillStyle = '#555';
      ctx.font = '13px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('Start a run to see agent movement', canvas.width / 2, canvas.height / 2);
      ctx.textAlign = 'start';
    }
  }, [trajectory, playing, gridSize, cellSize, drawFrame]);

  // Animation loop
  useEffect(() => {
    if (!trajectory || !playing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    stepRef.current = 0;

    const totalSteps = trajectory.steps.length;
    const speed = Math.max(30, 1500 / totalSteps);

    const tick = () => {
      if (stepRef.current >= totalSteps) {
        setPlaying(false);
        return;
      }
      drawFrame(ctx, trajectory, stepRef.current, gridSize, cellSize);
      stepRef.current++;
      animRef.current = setTimeout(tick, speed);
    };

    tick();
    return () => {
      if (animRef.current) clearTimeout(animRef.current);
    };
  }, [trajectory, playing, gridSize, cellSize, drawFrame]);

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-400">Grid View — Episode Replay</h3>
        <div className="flex items-center gap-2">
          {trajectory && (
            <span className="text-xs text-green-400">
              {trajectory.steps.length} steps
            </span>
          )}
          {trajectory && (
            <button
              onClick={() => setPlaying(!playing)}
              className={`px-3 py-1 rounded text-xs font-medium ${
                playing ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {playing ? 'Pause' : 'Replay'}
            </button>
          )}
        </div>
      </div>
      <canvas
        ref={canvasRef}
        width={CANVAS_SIZE}
        height={CANVAS_SIZE}
        className="rounded border border-gray-700"
      />
      <div className="flex gap-4 mt-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ background: COLORS.target }}></span> Target
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded" style={{ background: COLORS.obstacle }}></span> Obstacle
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ background: COLORS.agentA }}></span> Agent A (RNN)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ background: COLORS.agentB }}></span> Agent B (CNN)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ background: COLORS.agentC }}></span> Agent C (GNN)
        </span>
      </div>
    </div>
  );
}
