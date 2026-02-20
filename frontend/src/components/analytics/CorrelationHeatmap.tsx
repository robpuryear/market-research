"use client";
import { useCorrelation } from "@/hooks/useAnalytics";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

function cellColor(v: number): string {
  // Red for -1, white for 0, green for +1
  if (v >= 0) {
    const g = Math.round(255 * v);
    return `rgb(${255 - g}, 255, ${255 - g})`;
  } else {
    const r = Math.round(255 * -v);
    return `rgb(255, ${255 - r}, ${255 - r})`;
  }
}

function textColor(v: number): string {
  return Math.abs(v) > 0.5 ? "text-gray-800 font-semibold" : "text-gray-600";
}

export function CorrelationHeatmap() {
  const { data, error, isLoading } = useCorrelation();

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-sm text-gray-500 font-mono">Loading correlation matrix…</div>
      </div>
    );
  }

  if (error || !data || data.tickers.length === 0) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-sm text-red-500 font-mono">Failed to load correlation data</div>
      </div>
    );
  }

  const { tickers, matrix } = data;

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="text-sm font-semibold text-gray-700 font-mono flex items-center gap-1">
          Correlation Heatmap <InfoIcon tooltip={TOOLTIPS.correlationMatrix} />
        </div>
        <div className="text-xs text-gray-500 mt-0.5">3-month pairwise return correlations — red (−1) → green (+1)</div>
      </div>
      <div className="overflow-x-auto p-4">
        <table className="text-xs font-mono border-collapse">
          <thead>
            <tr>
              <th className="w-14" />
              {tickers.map((t) => (
                <th key={t} className="px-1 py-1 text-center text-gray-500 font-semibold min-w-[44px]">
                  {t}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map((rowTicker, ri) => (
              <tr key={rowTicker}>
                <td className="px-1 py-0.5 text-gray-500 font-semibold text-right pr-2 whitespace-nowrap">
                  {rowTicker}
                </td>
                {tickers.map((_, ci) => {
                  const v = matrix[ri]?.[ci] ?? 0;
                  return (
                    <td
                      key={ci}
                      className={`px-1 py-0.5 text-center min-w-[44px] ${textColor(v)}`}
                      style={{ backgroundColor: cellColor(v) }}
                      title={`${rowTicker} vs ${tickers[ci]}: ${v.toFixed(3)}`}
                    >
                      {v.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
