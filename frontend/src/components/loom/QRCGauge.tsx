/**
 * QRCGauge — SVG arc gauge showing Query-Response Coupling (0→1).
 *
 * Colour zones:
 *   0.0–0.5  → red    (uncoupled)
 *   0.5–0.8  → yellow (emerging)
 *   0.8–1.0  → green  (locked)
 *
 * Pulses when QRC = 1.000.
 */

import Tooltip from '../Tooltip';

interface Props {
  qrc: number | null;
}

const CX = 60;
const CY = 60;
const R = 48;
const START_ANGLE = -210; // degrees — leftmost point of arc
const SWEEP = 240;        // degrees total arc

function polarToXY(angle: number, r: number) {
  const rad = (angle * Math.PI) / 180;
  return {
    x: CX + r * Math.cos(rad),
    y: CY + r * Math.sin(rad),
  };
}

function arcPath(startDeg: number, endDeg: number, r: number) {
  const s = polarToXY(startDeg, r);
  const e = polarToXY(endDeg, r);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
}

function zoneColour(value: number): string {
  if (value < 0.5) return '#ef4444'; // red
  if (value < 0.8) return '#eab308'; // yellow
  return '#22c55e';                  // green
}

export default function QRCGauge({ qrc }: Props) {
  const value = qrc ?? 0;
  const clamped = Math.min(Math.max(value, 0), 1);
  const needleAngle = START_ANGLE + clamped * SWEEP;
  const colour = zoneColour(clamped);
  const isPulsing = value >= 0.999;

  const needleTip = polarToXY(needleAngle, R - 10);
  const needleBase1 = polarToXY(needleAngle + 90, 5);
  const needleBase2 = polarToXY(needleAngle - 90, 5);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-gray-400 uppercase tracking-wide">QRC</span>
        <Tooltip content="Are questions reliably getting answered? Red = agents guessing. Yellow = pattern forming. Green = locked in." />
      </div>
      <span className="text-[10px] text-gray-600 text-center">Query-Response Coupling</span>
      <div className={isPulsing ? 'animate-pulse' : ''}>
        <svg width="120" height="80" viewBox="0 0 120 80">
          {/* Background arc */}
          <path
            d={arcPath(START_ANGLE, START_ANGLE + SWEEP, R)}
            fill="none"
            stroke="#374151"
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Coloured filled arc */}
          {clamped > 0 && (
            <path
              d={arcPath(START_ANGLE, needleAngle, R)}
              fill="none"
              stroke={colour}
              strokeWidth="8"
              strokeLinecap="round"
            />
          )}
          {/* Needle */}
          <polygon
            points={`${needleTip.x},${needleTip.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
            fill={colour}
          />
          {/* Centre dot */}
          <circle cx={CX} cy={CY} r={4} fill={colour} />
        </svg>
      </div>
      <span className="text-sm font-mono" style={{ color: colour }}>
        {qrc !== null ? qrc.toFixed(3) : 'N/A'}
      </span>
    </div>
  );
}
