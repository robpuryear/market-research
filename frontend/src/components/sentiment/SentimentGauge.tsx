"use client";
import { useRedditSentiment } from "@/hooks/useSentiment";

export function SentimentGauge() {
  const { data } = useRedditSentiment();
  if (!data) return null;

  const mentions = data.ticker_mentions;
  if (!mentions.length) return null;

  const avgScore = mentions.reduce((s, m) => s + m.sentiment_score, 0) / mentions.length;
  const normalized = ((avgScore + 1) / 2) * 100; // -1..1 → 0..100

  const label = normalized >= 65 ? "Bullish" : normalized >= 50 ? "Neutral" : normalized >= 35 ? "Mixed" : "Bearish";
  const color = normalized >= 65 ? "text-green-600" : normalized >= 50 ? "text-gray-700" : normalized >= 35 ? "text-amber-600" : "text-red-600";

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">Reddit Sentiment</div>
      <div className={`text-3xl font-bold font-mono ${color}`}>{label}</div>
      <div className="mt-3 bg-gray-100 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${normalized >= 65 ? "bg-green-500" : normalized >= 50 ? "bg-gray-400" : normalized >= 35 ? "bg-yellow-500" : "bg-red-500"}`}
          style={{ width: `${normalized}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-600 mt-1">
        <span>Bearish</span><span>Neutral</span><span>Bullish</span>
      </div>
      <div className="text-xs text-gray-600 mt-2">
        Score: {avgScore >= 0 ? "+" : ""}{avgScore.toFixed(3)} · {mentions.length} tickers tracked
      </div>
    </div>
  );
}
