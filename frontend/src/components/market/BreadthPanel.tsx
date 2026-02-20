"use client";
import { useBreadth } from "@/hooks/useMarketData";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

function MaBar({ label, pct, tooltip }: { label: string; pct: number; tooltip?: string }) {
  const color = pct >= 70 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span className="flex items-center gap-1">
          Above {label}
          {tooltip && <InfoIcon tooltip={tooltip} />}
        </span>
        <span className="font-mono font-bold text-gray-800">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function BreadthPanel() {
  const { data, isLoading, error } = useBreadth();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 text-sm p-4">{error.message}</div>;
  if (!data) return null;

  const total = data.advancers + data.decliners + data.unchanged;
  const advPct = total > 0 ? (data.advancers / total) * 100 : 0;
  const decPct = total > 0 ? (data.decliners / total) * 100 : 0;

  const scoreColor =
    data.breadth_score >= 65 ? "text-green-600" :
    data.breadth_score >= 40 ? "text-amber-600" : "text-red-600";

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold text-gray-700 uppercase tracking-widest">Market Breadth</div>
        <div className={`text-2xl font-bold font-mono ${scoreColor}`}>
          {data.breadth_score.toFixed(1)}
          <span className="text-xs text-gray-500 font-normal ml-1">/ 100</span>
        </div>
      </div>

      {/* Advancer/Decliner bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span className="text-green-600">{data.advancers} adv</span>
          <span className="text-gray-500">{data.unchanged} unch</span>
          <span className="text-red-600">{data.decliners} dec</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
          <div className="h-full bg-green-500" style={{ width: `${advPct}%` }} />
          <div className="h-full bg-red-500 ml-auto" style={{ width: `${decPct}%` }} />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span className="flex items-center gap-1">
            A/D ratio: <span className="text-gray-500 font-mono">{data.advance_decline_ratio.toFixed(2)}</span>
            <InfoIcon tooltip={TOOLTIPS.advanceDecline} />
          </span>
          <span className="flex items-center gap-1">
            Avg RSI: <span className="text-gray-500 font-mono">{data.avg_rsi.toFixed(1)}</span>
            <InfoIcon tooltip={TOOLTIPS.rsi} />
          </span>
        </div>
      </div>

      {/* MA bars */}
      <div className="space-y-2.5">
        <MaBar label="20-day MA" pct={data.pct_above_20ma} tooltip={TOOLTIPS.ma20Breadth} />
        <MaBar label="50-day MA" pct={data.pct_above_50ma} tooltip={TOOLTIPS.ma50Breadth} />
        <MaBar label="200-day MA" pct={data.pct_above_200ma} tooltip={TOOLTIPS.ma200Breadth} />
      </div>

      {/* 52w hi/lo */}
      <div className="flex gap-4 text-xs">
        <div className="flex-1 bg-white rounded p-2 text-center">
          <div className="text-gray-500 mb-0.5 flex items-center justify-center gap-1">
            52W New Highs <InfoIcon tooltip={TOOLTIPS.newHighsLows} />
          </div>
          <div className="text-green-600 font-bold font-mono text-base">{data.new_highs_52w}</div>
        </div>
        <div className="flex-1 bg-white rounded p-2 text-center">
          <div className="text-gray-500 mb-0.5">52W New Lows</div>
          <div className="text-red-600 font-bold font-mono text-base">{data.new_lows_52w}</div>
        </div>
      </div>
    </div>
  );
}
