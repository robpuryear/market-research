"use client";
import { useIV } from "@/hooks/useMarketData";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

export function IVAnalyticsPanel({ ticker }: { ticker: string }) {
  const { data, isLoading, error } = useIV(ticker);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 text-sm p-4">{error.message}</div>;
  if (!data || data.atm_iv === 0) return null;

  const rankColor =
    data.iv_rank >= 70 ? "text-red-600" :
    data.iv_rank >= 40 ? "text-amber-600" : "text-green-600";

  const skewColor = data.put_call_skew > 0.02 ? "text-red-600" : data.put_call_skew < -0.02 ? "text-green-600" : "text-gray-700";

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-5 space-y-4">
      <div className="text-xs font-semibold text-gray-700 uppercase tracking-widest">IV Analytics</div>

      {/* IV rank bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span className="flex items-center gap-1">
            IV Rank <InfoIcon tooltip={TOOLTIPS.ivRank} />
          </span>
          <span className={`font-mono font-bold ${rankColor}`}>{data.iv_rank.toFixed(1)}</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${data.iv_rank >= 70 ? "bg-red-500" : data.iv_rank >= 40 ? "bg-yellow-500" : "bg-green-500"}`}
            style={{ width: `${Math.min(data.iv_rank, 100)}%` }}
          />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white rounded p-3">
          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
            ATM IV <InfoIcon tooltip={TOOLTIPS.atmIV} />
          </div>
          <div className="text-gray-800 font-mono font-bold">{(data.atm_iv * 100).toFixed(1)}%</div>
        </div>
        <div className="bg-white rounded p-3">
          <div className="text-xs text-gray-500 mb-1">Put/Call Skew</div>
          <div className={`font-mono font-bold ${skewColor}`}>
            {data.put_call_skew >= 0 ? "+" : ""}{(data.put_call_skew * 100).toFixed(2)}%
          </div>
        </div>
        <div className="bg-white rounded p-3">
          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
            Expected Move 1W <InfoIcon tooltip={TOOLTIPS.expectedMoveWeekly} />
          </div>
          <div className="text-gray-800 font-mono font-bold">±${data.expected_move_1w.toFixed(2)}</div>
        </div>
        <div className="bg-white rounded p-3">
          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
            Expected Move 1M <InfoIcon tooltip={TOOLTIPS.expectedMoveMonthly} />
          </div>
          <div className="text-gray-800 font-mono font-bold">±${data.expected_move_1m.toFixed(2)}</div>
        </div>
      </div>

      {/* Term structure */}
      {data.term_structure.length >= 2 && (
        <div>
          <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
            Term Structure (nearest expiries) <InfoIcon tooltip={TOOLTIPS.ivTermStructure} />
          </div>
          <div className="flex items-end gap-1 h-12">
            {data.term_structure.map((iv, i) => {
              const maxIV = Math.max(...data.term_structure);
              const heightPct = maxIV > 0 ? (iv / maxIV) * 100 : 0;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div
                    className="w-full bg-purple-600 rounded-sm"
                    style={{ height: `${heightPct}%`, minHeight: "4px" }}
                  />
                  <div className="text-xs text-gray-500 font-mono">{(iv * 100).toFixed(0)}%</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
