/**
 * TypeEntropyCoolingBar — horizontal bar showing how "cool" (crystallised)
 * the signal type distribution has become.
 *
 * Width  ∝  current type_entropy / log(3)  (max bits for 3 types ≈ 1.585)
 * Colour: orange (H=max) → blue (H=0)
 */

import Tooltip from '../Tooltip';

interface Props {
  typeEntropy: number | null;
}

const MAX_ENTROPY = Math.log(3); // ≈ 1.585 nats

function interpolateColour(t: number): string {
  // t in [0,1]: 0=blue, 1=orange
  const r = Math.round(249 * t + 59 * (1 - t));
  const g = Math.round(115 * t + 130 * (1 - t));
  const b = Math.round(22 * t + 246 * (1 - t));
  return `rgb(${r},${g},${b})`;
}

export default function TypeEntropyCoolingBar({ typeEntropy }: Props) {
  const header = (
    <div className="flex items-center justify-between text-xs text-gray-400">
      <div className="flex items-center gap-1.5">
        <span className="uppercase tracking-wide">Type Entropy</span>
        <Tooltip content="How mixed is the communication? Orange = all three signal types used equally (chaotic). Blue = one type dominates (crystallised language)." />
      </div>
      {typeEntropy !== null && <span>{typeEntropy.toFixed(3)} nats</span>}
    </div>
  );

  if (typeEntropy === null) {
    return (
      <div className="flex flex-col gap-1">
        {header}
        <div className="h-6 bg-gray-800 rounded text-xs text-gray-500 flex items-center px-2">
          N/A — Protocol 0
        </div>
        <span className="text-[10px] text-gray-600">Not measured in baseline runs</span>
      </div>
    );
  }

  const fraction = Math.min(Math.max(typeEntropy / MAX_ENTROPY, 0), 1);
  const colour = interpolateColour(fraction);

  return (
    <div className="flex flex-col gap-1">
      {header}
      <div className="h-5 bg-gray-800 rounded overflow-hidden">
        <div
          className="h-full rounded transition-all duration-300"
          style={{ width: `${fraction * 100}%`, backgroundColor: colour }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-600">
        <span>crystallised</span>
        <span>uniform</span>
      </div>
    </div>
  );
}
