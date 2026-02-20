"use client";
import { useState } from "react";
import { useSignals } from "@/hooks/useAnalytics";
import { useSqueeze } from "@/hooks/useAnalytics";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

function DirectionBadge({ direction }: { direction: string }) {
  if (direction === "bullish") {
    return (
      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-semibold">
        ▲ Bullish
      </span>
    );
  }
  if (direction === "bearish") {
    return (
      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-semibold">
        ▼ Bearish
      </span>
    );
  }
  return (
    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-semibold">
      ◆ Neutral
    </span>
  );
}

function SignalCard({ signal_type, direction, description }: {
  signal_type: string;
  direction: string;
  description: string;
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-3 flex items-start justify-between gap-3 bg-gray-50">
      <div>
        <div className="text-sm font-semibold text-gray-800 font-mono">{signal_type}</div>
        <div className="text-xs text-gray-500 mt-0.5">{description}</div>
      </div>
      <DirectionBadge direction={direction} />
    </div>
  );
}

function TickerFeed({ ticker }: { ticker: string }) {
  const { data, error, isLoading } = useSignals(ticker);

  if (isLoading) {
    return <div className="text-sm text-gray-400 font-mono py-4 text-center">Loading signals…</div>;
  }
  if (error) {
    return <div className="text-sm text-red-400 font-mono py-4 text-center">Failed to load signals</div>;
  }
  if (!data || data.signals.length === 0) {
    return (
      <div className="py-6 text-center">
        <div className="text-sm text-gray-400 font-mono">No signals firing for {ticker}</div>
        <div className="text-xs text-gray-400 mt-1">RSI: {data?.rsi?.toFixed(1) ?? "—"}</div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs text-gray-500 font-mono">
          {data.signal_count} signal{data.signal_count !== 1 ? "s" : ""} · RSI {data.rsi.toFixed(1)}
        </div>
        <div className="text-xs text-gray-400">
          {new Date(data.timestamp).toLocaleTimeString()}
        </div>
      </div>
      {data.signals.map((s, i) => (
        <SignalCard key={i} {...s} />
      ))}
    </div>
  );
}

export function MLSignalsFeed() {
  const { data: squeezeData } = useSqueeze();
  const tickers = squeezeData?.map((s) => s.ticker) ?? [];
  const [selectedTicker, setSelectedTicker] = useState<string>("");

  const activeTicker = selectedTicker || tickers[0] || "";

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="text-sm font-semibold text-gray-700 font-mono flex items-center gap-1">
          ML Signals Feed <InfoIcon tooltip={TOOLTIPS.mlSignalsFeed} />
        </div>
        <div className="text-xs text-gray-500 mt-0.5">Technical signals per ticker</div>
      </div>
      <div className="p-4">
        {tickers.length > 0 && (
          <div className="mb-4">
            <select
              value={activeTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="text-sm font-mono border border-gray-300 rounded px-2 py-1.5 bg-white text-gray-700 focus:outline-none focus:border-blue-400"
            >
              {tickers.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        )}
        {activeTicker ? (
          <TickerFeed ticker={activeTicker} />
        ) : (
          <div className="text-sm text-gray-400 font-mono py-4 text-center">
            No tickers available — load squeeze data first
          </div>
        )}
      </div>
    </div>
  );
}
