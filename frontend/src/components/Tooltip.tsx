/**
 * Tooltip — hover-reveal plain-English panel description.
 * Shows a ? badge; on hover displays the content above it.
 */

interface Props {
  content: string;
}

export default function Tooltip({ content }: Props) {
  return (
    <div className="relative group inline-flex items-center">
      <span className="w-4 h-4 rounded-full bg-gray-700 hover:bg-gray-600 text-gray-400 hover:text-gray-200 text-[10px] flex items-center justify-center cursor-help transition-colors select-none">
        ?
      </span>
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50
                      invisible group-hover:visible opacity-0 group-hover:opacity-100
                      transition-opacity duration-150
                      bg-gray-800 border border-gray-600 text-gray-300 text-xs
                      rounded px-3 py-2 w-52 text-center shadow-xl pointer-events-none">
        {content}
        <div className="absolute top-full left-1/2 -translate-x-1/2
                        border-4 border-transparent border-t-gray-600" />
      </div>
    </div>
  );
}
