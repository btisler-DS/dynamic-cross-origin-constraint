/**
 * PCAScatterView — D3 scatter plot of 8-dim signal vectors projected onto
 * the first two principal components.
 *
 * Points coloured by type:
 *   DECLARE (0) → gray (#9ca3af)
 *   QUERY   (1) → amber (#f59e0b)
 *   RESPOND (2) → blue  (#60a5fa)
 *
 * Agent C points rendered as diamonds (expected to form the interstitial
 * broker cluster, then snap to a dedicated RESPOND zone at crystallisation).
 *
 * At crystallisation_epoch a ring-pulse is shown and a toast is triggered.
 */

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { PCAPoint } from '../../api/loom';
import Tooltip from '../Tooltip';

interface Props {
  points: PCAPoint[] | null;
  crystallizationEpoch: number | null;
  currentEpoch: number;
}

const TYPE_COLOURS: Record<number, string> = {
  0: '#9ca3af', // DECLARE — gray
  1: '#f59e0b', // QUERY   — amber
  2: '#60a5fa', // RESPOND — blue
};

const TYPE_LABELS: Record<number, string> = {
  0: 'DECLARE',
  1: 'QUERY',
  2: 'RESPOND',
};

const W = 320;
const H = 220;
const PAD = { top: 16, right: 16, bottom: 28, left: 36 };

export default function PCAScatterView({ points, crystallizationEpoch, currentEpoch }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [showToast, setShowToast] = useState(false);
  const prevEpochRef = useRef<number>(-1);

  // Trigger toast when scrubber first hits crystallisation epoch
  useEffect(() => {
    if (
      crystallizationEpoch !== null &&
      prevEpochRef.current < crystallizationEpoch &&
      currentEpoch >= crystallizationEpoch
    ) {
      setShowToast(true);
      const timer = setTimeout(() => setShowToast(false), 3000);
      return () => clearTimeout(timer);
    }
    prevEpochRef.current = currentEpoch;
  }, [currentEpoch, crystallizationEpoch]);

  useEffect(() => {
    if (!svgRef.current || !points || points.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const innerW = W - PAD.left - PAD.right;
    const innerH = H - PAD.top - PAD.bottom;

    const xExt = d3.extent(points, (d) => d.pc1) as [number, number];
    const yExt = d3.extent(points, (d) => d.pc2) as [number, number];

    const xScale = d3.scaleLinear().domain(xExt).nice().range([0, innerW]);
    const yScale = d3.scaleLinear().domain(yExt).nice().range([innerH, 0]);

    const g = svg.append('g').attr('transform', `translate(${PAD.left},${PAD.top})`);

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(4).tickSize(3))
      .selectAll('text, line, path')
      .style('fill', '#6b7280')
      .style('stroke', '#4b5563');

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(4).tickSize(3))
      .selectAll('text, line, path')
      .style('fill', '#6b7280')
      .style('stroke', '#4b5563');

    // Axis labels
    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 22)
      .attr('text-anchor', 'middle')
      .attr('fill', '#6b7280')
      .attr('font-size', 9)
      .text('PC1');

    g.append('text')
      .attr('x', -innerH / 2)
      .attr('y', -28)
      .attr('text-anchor', 'middle')
      .attr('transform', 'rotate(-90)')
      .attr('fill', '#6b7280')
      .attr('font-size', 9)
      .text('PC2');

    // Points
    points.forEach((p) => {
      const cx = xScale(p.pc1);
      const cy = yScale(p.pc2);
      const colour = TYPE_COLOURS[p.type_int] ?? '#ffffff';
      const isAgentC = p.agent === 'C';

      if (isAgentC) {
        // Diamond shape for Agent C
        const s = 5;
        g.append('polygon')
          .attr('points', `${cx},${cy - s} ${cx + s},${cy} ${cx},${cy + s} ${cx - s},${cy}`)
          .attr('fill', colour)
          .attr('opacity', 0.8)
          .append('title')
          .text(`C | ${TYPE_LABELS[p.type_int] ?? p.type_int}`);
      } else {
        g.append('circle')
          .attr('cx', cx)
          .attr('cy', cy)
          .attr('r', 3.5)
          .attr('fill', colour)
          .attr('opacity', 0.75)
          .append('title')
          .text(`${p.agent} | ${TYPE_LABELS[p.type_int] ?? p.type_int}`);
      }
    });

    // Crystallisation ring pulse (static ring at centre when at/past that epoch)
    if (crystallizationEpoch !== null && currentEpoch >= crystallizationEpoch) {
      g.append('circle')
        .attr('cx', innerW / 2)
        .attr('cy', innerH / 2)
        .attr('r', Math.min(innerW, innerH) * 0.42)
        .attr('fill', 'none')
        .attr('stroke', '#22c55e')
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6 3')
        .attr('opacity', 0.4);
    }
  }, [points, crystallizationEpoch, currentEpoch]);

  const panelHeader = (
    <div className="flex items-center gap-1.5 mb-1">
      <span className="text-xs text-gray-400 uppercase tracking-wide">Signal Clusters</span>
      <Tooltip content="Each dot is a signal sent between agents. Tight clusters mean agents have developed consistent roles — one for statements, one for questions, one for answers." />
    </div>
  );

  if (!points || points.length === 0) {
    return (
      <div className="flex flex-col h-full">
        {panelHeader}
        <div className="flex-1 flex items-center justify-center text-xs text-gray-500 text-center px-4">
          PCA unavailable — signal samples not recorded in this run.
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col">
      {panelHeader}
      {/* Legend */}
      <div className="flex gap-3 mb-1">
        {Object.entries(TYPE_LABELS).map(([k, label]) => (
          <span key={k} className="flex items-center gap-1 text-xs">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: TYPE_COLOURS[Number(k)] }}
            />
            {label}
          </span>
        ))}
        <span className="flex items-center gap-1 text-xs text-gray-400">
          ◆ Agent C
        </span>
      </div>
      <svg ref={svgRef} width={W} height={H} className="bg-gray-900 rounded" />
      {/* Phase transition toast */}
      {showToast && (
        <div className="absolute top-8 left-1/2 -translate-x-1/2 bg-green-900 border border-green-500 text-green-300 text-xs px-3 py-1.5 rounded shadow-lg animate-pulse whitespace-nowrap z-10">
          Phase Transition Detected — E{crystallizationEpoch}
        </div>
      )}
    </div>
  );
}
