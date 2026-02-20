"use client";
import { useMarketSnapshot } from "@/hooks/useMarketData";
import { LoadingCard } from "@/components/ui/LoadingSpinner";
import { ChangeText } from "@/components/ui/Badge";
import type { IndexData } from "@/lib/types";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

const TICKER_TOOLTIPS: Record<string, string> = {
  SPY: TOOLTIPS.spy,
  QQQ: TOOLTIPS.qqq,
  IWM: TOOLTIPS.iwm,
};

function IndexCard({ data }: { data: IndexData }) {
  const tooltip = TICKER_TOOLTIPS[data.ticker];
  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-blue-600 font-bold font-mono flex items-center gap-1">
          {data.ticker}
          {tooltip && <InfoIcon tooltip={tooltip} />}
        </span>
        {data.above_200ma != null && (
          <span className={`text-xs ${data.above_200ma ? "text-green-600" : "text-red-600"}`}>
            {data.above_200ma ? "▲ > 200MA" : "▼ < 200MA"}
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-gray-900 font-mono">${data.price.toFixed(2)}</div>
      <div className="mt-1 flex items-center gap-3 text-sm">
        <ChangeText value={data.change_pct} />
        {data.rsi && (
          <span className="text-gray-500 flex items-center gap-1">
            RSI: <span className={`font-mono ${data.rsi > 70 ? "text-red-600" : data.rsi < 30 ? "text-green-600" : "text-gray-700"}`}>{data.rsi.toFixed(1)}</span>
            <InfoIcon tooltip={TOOLTIPS.rsi} />
          </span>
        )}
        {data.volume_ratio && (
          <span className="text-gray-500 flex items-center gap-1">
            Vol: <span className="text-gray-700 font-mono">{data.volume_ratio.toFixed(1)}x</span>
            <InfoIcon tooltip={TOOLTIPS.volumeRatio} />
          </span>
        )}
      </div>
      <div className="mt-2 grid grid-cols-3 gap-1 text-xs text-gray-500">
        {data.ma_20 && <span>MA20: <span className="text-amber-600">${data.ma_20.toFixed(0)}</span></span>}
        {data.ma_50 && <span>MA50: <span className="text-blue-600">${data.ma_50.toFixed(0)}</span></span>}
        {data.ma_200 && <span>MA200: <span className="text-orange-600">${data.ma_200.toFixed(0)}</span></span>}
      </div>
    </div>
  );
}

export function IndexLevels() {
  const { data, isLoading } = useMarketSnapshot();

  if (isLoading) return <div className="grid grid-cols-3 gap-4">{[...Array(3)].map((_, i) => <LoadingCard key={i} />)}</div>;
  if (!data) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <IndexCard data={data.spy} />
      <IndexCard data={data.qqq} />
      <IndexCard data={data.iwm} />
    </div>
  );
}
