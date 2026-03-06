"use client";
import { useState, useEffect } from "react";
import { fetchTrending, addToWatchlist } from "@/lib/api";
import type { TrendingStock } from "@/lib/types";
import { ChangeText } from "@/components/ui/Badge";
import { clsx } from "clsx";
import { mutate } from "swr";

const SOURCE_STYLES: Record<string, string> = {
  Reddit:     "bg-orange-100 text-orange-700",
  News:       "bg-blue-100 text-blue-700",
  StockTwits: "bg-purple-100 text-purple-700",
  Yahoo:      "bg-violet-100 text-violet-700",
};

function SourceBadges({ sources }: { sources: string[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {sources.map((s) => (
        <span key={s} className={clsx("px-1 py-0.5 rounded text-xs font-medium", SOURCE_STYLES[s] ?? "bg-gray-100 text-gray-600")}>
          {s}
        </span>
      ))}
    </div>
  );
}

function MomentumBar({ score }: { score: number }) {
  const pct = Math.min(score, 100);
  const color = score >= 70 ? "bg-emerald-500" : score >= 45 ? "bg-amber-500" : "bg-blue-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={clsx("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-700">{score.toFixed(0)}</span>
    </div>
  );
}

export function TrendingStocks() {
  const [stocks, setStocks] = useState<TrendingStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null);

  useEffect(() => {
    fetchTrending(15)
      .then(setStocks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleAdd = async (ticker: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setAdding(ticker);
    try {
      await addToWatchlist(ticker);
      mutate("watchlist");
      setStocks((prev) => prev.map((s) => s.ticker === ticker ? { ...s, on_watchlist: true } : s));
    } catch (err) {
      alert(`Failed to add ${ticker}: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setAdding(null);
    }
  };

  if (loading) return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <h2 className="text-sm font-bold text-gray-700 font-mono mb-3">◉ Trending &amp; Momentum</h2>
      <div className="text-xs text-gray-400 animate-pulse">Scanning Reddit, news, StockTwits, Yahoo Finance…</div>
    </div>
  );

  if (error) return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <h2 className="text-sm font-bold text-gray-700 font-mono mb-2">◉ Trending &amp; Momentum</h2>
      <div className="text-xs text-red-500">Failed to load trending stocks: {error}</div>
    </div>
  );

  if (!stocks.length) return null;

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-bold text-gray-700 font-mono">◉ Trending &amp; Momentum</h2>
        <span className="text-xs text-gray-400">
          Reddit · AV News · StockTwits · Yahoo · sorted by momentum score
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead className="border-b border-gray-200">
            <tr>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Ticker</th>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Price</th>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Change</th>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Vol</th>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Sources</th>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Buzz</th>
              <th className="text-left py-2 px-3 text-gray-500 uppercase tracking-wider">Momentum</th>
              <th className="py-2 px-3" />
            </tr>
          </thead>
          <tbody>
            {stocks.map((s) => (
              <tr key={s.ticker} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 px-3">
                  <div className="font-bold text-gray-800">{s.ticker}</div>
                  <div className="text-gray-400 truncate max-w-[110px]">{s.company_name}</div>
                </td>
                <td className="py-2 px-3 text-gray-800">${s.price.toFixed(2)}</td>
                <td className="py-2 px-3"><ChangeText value={s.change_pct} /></td>
                <td className={clsx("py-2 px-3", s.volume_ratio > 2 ? "text-amber-600" : "text-gray-500")}>
                  {s.volume_ratio.toFixed(1)}x
                </td>
                <td className="py-2 px-3"><SourceBadges sources={s.buzz_sources} /></td>
                <td className="py-2 px-3 text-gray-500">
                  {s.reddit_mentions > 0 && <div>{s.reddit_mentions} Reddit</div>}
                  {s.news_mentions > 0 && <div>{s.news_mentions} news</div>}
                </td>
                <td className="py-2 px-3"><MomentumBar score={s.momentum_score} /></td>
                <td className="py-2 px-3 text-right">
                  {s.on_watchlist ? (
                    <span className="text-gray-400">✓ Watching</span>
                  ) : (
                    <button
                      onClick={(e) => handleAdd(s.ticker, e)}
                      disabled={adding === s.ticker}
                      className="text-blue-600 hover:text-blue-800 disabled:text-gray-300 font-semibold transition-colors"
                    >
                      {adding === s.ticker ? "Adding…" : "+ Watch"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
