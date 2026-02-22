"use client";
import { useState } from "react";
import { useCompositeSentiment } from "@/hooks/useAnalytics";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { WATCHLIST_TICKERS } from "@/lib/constants";
import { InfoIcon } from "@/components/ui/InfoIcon";
import { TOOLTIPS } from "@/lib/tooltips";

const SCORE_COLOR = (score: number) => {
  if (score >= 60) return "text-green-600";
  if (score >= 20) return "text-emerald-600";
  if (score <= -60) return "text-red-600";
  if (score <= -20) return "text-orange-600";
  return "text-gray-700";
};

const SCORE_BG = (score: number) => {
  if (score >= 60) return "bg-green-100/40 border-green-300";
  if (score >= 20) return "bg-emerald-100/40 border-emerald-300";
  if (score <= -60) return "bg-red-100/40 border-red-300";
  if (score <= -20) return "bg-orange-100/40 border-orange-300";
  return "bg-gray-100 border-gray-300";
};

const LABEL_COLOR = (label: string) => {
  if (label.includes("Very Bullish")) return "bg-green-600 text-white";
  if (label.includes("Bullish")) return "bg-emerald-600 text-white";
  if (label.includes("Very Bearish")) return "bg-red-600 text-white";
  if (label.includes("Bearish")) return "bg-orange-600 text-white";
  return "bg-gray-600 text-white";
};

function CompositeSentimentMeter({ ticker }: { ticker: string }) {
  const { data, isLoading } = useCompositeSentiment(ticker);

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-6 flex items-center justify-center min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data || data.confidence === 0) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-6">
        <div className="text-sm text-gray-500 text-center py-8">
          Insufficient data to calculate composite sentiment for {ticker}
        </div>
      </div>
    );
  }

  const scorePercent = ((data.composite_score + 100) / 200) * 100; // Convert -100/+100 to 0-100%

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-6">
      {/* Header with ticker and label */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-lg font-mono font-bold text-blue-600">{ticker}</span>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${LABEL_COLOR(data.composite_label)}`}>
            {data.composite_label}
          </span>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold font-mono ${SCORE_COLOR(data.composite_score)}`}>
            {data.composite_score >= 0 ? "+" : ""}{data.composite_score.toFixed(0)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Confidence: {(data.confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Score gauge */}
      <div className="mb-6">
        <div className="relative h-3 bg-gradient-to-r from-red-500 via-gray-300 to-green-500 rounded-full overflow-hidden">
          <div
            className="absolute top-0 h-full w-1 bg-gray-900 shadow-lg"
            style={{ left: `${scorePercent}%`, transform: "translateX(-50%)" }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>-100 Bearish</span>
          <span>0 Neutral</span>
          <span>+100 Bullish</span>
        </div>
      </div>

      {/* Components breakdown */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
          Component Breakdown
        </div>
        {data.components.map((component, idx) => {
          const componentScorePercent = ((component.score + 1) / 2) * 100; // Convert -1/+1 to 0-100%
          const componentColor = component.score >= 0.3 ? "bg-green-500" : component.score <= -0.3 ? "bg-red-500" : "bg-gray-400";

          return (
            <div key={idx} className="border border-gray-200 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-800">{component.name}</span>
                  <span className="text-xs text-gray-500">
                    (weight: {(component.weight * 100).toFixed(0)}%)
                  </span>
                </div>
                <span className={`text-sm font-mono font-semibold ${component.score >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {component.score >= 0 ? "+" : ""}{component.score.toFixed(2)}
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-1">
                <div
                  className={`h-full ${componentColor} transition-all`}
                  style={{ width: `${componentScorePercent}%` }}
                />
              </div>
              <div className="text-xs text-gray-600">{component.description}</div>
              <div className="text-xs text-gray-500 mt-1">
                Confidence: {(component.confidence * 100).toFixed(0)}%
              </div>
            </div>
          );
        })}
      </div>

      {data.components.length === 0 && (
        <div className="text-sm text-gray-500 text-center py-4 border border-gray-200 rounded">
          No sentiment components available
        </div>
      )}
    </div>
  );
}

export function CompositeSentimentPanel() {
  const tickers = WATCHLIST_TICKERS.filter((t) => !["SPY", "QQQ", "IWM"].includes(t));
  const [selected, setSelected] = useState(tickers[0] || "NVDA");

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest">
            Composite Sentiment Score
          </div>
          <InfoIcon tooltip={TOOLTIPS.compositeSentiment || "Multi-factor sentiment combining news, analyst ratings, insider activity, options flow, and technical momentum. Score ranges from -100 (very bearish) to +100 (very bullish)."} />
        </div>
        <div className="flex gap-1 flex-wrap justify-end">
          {tickers.map((t) => (
            <button
              key={t}
              onClick={() => setSelected(t)}
              className={`px-2 py-0.5 text-xs rounded font-mono transition-colors ${
                selected === t
                  ? "bg-purple-700 text-white"
                  : "bg-gray-50 text-gray-500 hover:bg-gray-100"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <CompositeSentimentMeter ticker={selected} />
    </div>
  );
}
