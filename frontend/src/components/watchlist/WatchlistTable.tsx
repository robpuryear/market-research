"use client";
import { useState, useEffect } from "react";
import { useWatchlist } from "@/hooks/useWatchlist";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ChangeText } from "@/components/ui/Badge";
import { useRouter } from "next/navigation";
import type { StockData, CompositeSentiment } from "@/lib/types";
import { clsx } from "clsx";
import { removeFromWatchlist, fetchCompositeSentiment } from "@/lib/api";
import { mutate } from "swr";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

type SortKey = keyof StockData;

function SentimentBadge({ sentiment }: { sentiment?: CompositeSentiment }) {
  if (!sentiment) return <span className="text-gray-400 text-xs">…</span>;
  const score = sentiment.composite_score;
  const label = sentiment.composite_label;
  const colorClass =
    score >= 60 ? "text-emerald-600" :
    score >= 20 ? "text-green-500" :
    score <= -60 ? "text-red-600" :
    score <= -20 ? "text-red-400" :
    "text-gray-500";
  return (
    <span className={clsx("font-semibold", colorClass)} title={label}>
      {score > 0 ? "+" : ""}{score.toFixed(0)}
      <span className="font-normal text-gray-400 ml-1 text-xs">{label.replace("Very ", "V.")}</span>
    </span>
  );
}

export function WatchlistTable({ compact = false }: { compact?: boolean }) {
  const { data, isLoading, error } = useWatchlist();
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("change_pct");
  const [sortAsc, setSortAsc] = useState(false);
  const [filter, setFilter] = useState("");
  const [removingTicker, setRemovingTicker] = useState<string | null>(null);
  const [sentiments, setSentiments] = useState<Record<string, CompositeSentiment>>({});

  useEffect(() => {
    if (!data) return;
    data.forEach((s) => {
      if (sentiments[s.ticker]) return;
      fetchCompositeSentiment(s.ticker)
        .then((r) => setSentiments((prev) => ({ ...prev, [s.ticker]: r })))
        .catch(() => {/* silently skip */});
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  }

  const handleRemove = async (ticker: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click
    if (!confirm(`Remove ${ticker} from watchlist?`)) return;

    setRemovingTicker(ticker);
    try {
      await removeFromWatchlist(ticker);
      mutate("watchlist"); // Refresh the watchlist
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      alert(`Failed to remove ${ticker}: ${message}`);
    } finally {
      setRemovingTicker(null);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 text-sm p-4">{error.message}</div>;
  if (!data) return null;

  const filtered = data.filter((s) =>
    s.ticker.toLowerCase().includes(filter.toLowerCase())
  );
  const sorted = [...filtered].sort((a, b) => {
    const va = (a[sortKey] as number) ?? -Infinity;
    const vb = (b[sortKey] as number) ?? -Infinity;
    return sortAsc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
  });

  const SortHeader = ({ k, label, tooltip }: { k: SortKey; label: string; tooltip?: string }) => (
    <th
      className="text-left py-2 px-3 text-gray-500 text-xs uppercase tracking-wider cursor-pointer hover:text-gray-700 select-none"
      onClick={() => handleSort(k)}
    >
      <span className="flex items-center gap-1">
        {label} {sortKey === k ? (sortAsc ? "▲" : "▼") : ""}
        {tooltip && <InfoIcon tooltip={tooltip} />}
      </span>
    </th>
  );

  return (
    <div>
      {!compact && (
        <div className="mb-3">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter tickers..."
            className="bg-white border border-gray-300 rounded px-3 py-1.5 text-sm text-gray-700 placeholder-gray-400 outline-none focus:border-blue-500 w-48"
          />
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead className="border-b border-gray-300">
            <tr>
              <SortHeader k="ticker" label="Ticker" />
              <SortHeader k="price" label="Price" />
              <SortHeader k="change_pct" label="Change" />
              <SortHeader k="volume_ratio" label="Vol Ratio" tooltip={TOOLTIPS.volumeRatio} />
              {!compact && (
                <>
                  <SortHeader k="analyst_rating" label="Rating" tooltip={TOOLTIPS.analystRating} />
                  <SortHeader k="price_target" label="P.Target" />
                  <SortHeader k="short_interest_pct" label="Short %" tooltip={TOOLTIPS.shortInterest} />
                  <SortHeader k="squeeze_score" label="Squeeze" tooltip={TOOLTIPS.squeezeScore} />
                </>
              )}
              <th className="text-left py-2 px-3 text-gray-500 text-xs">
                <span className="flex items-center gap-1">
                  Options <InfoIcon tooltip={TOOLTIPS.unusualOptions} />
                </span>
              </th>
              <th className="text-left py-2 px-3 text-gray-500 text-xs uppercase tracking-wider">Sentiment</th>
              {!compact && <th className="text-center py-2 px-3 text-gray-500 text-xs">Remove</th>}
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => (
              <tr
                key={s.ticker}
                className="border-b border-gray-300 hover:bg-gray-100 cursor-pointer"
                onClick={() => router.push(`/watchlist/${s.ticker}`)}
              >
                <td className="py-2 px-3 text-blue-600 font-bold">{s.ticker}</td>
                <td className="py-2 px-3 text-gray-800">${s.price.toFixed(2)}</td>
                <td className="py-2 px-3"><ChangeText value={s.change_pct} /></td>
                <td className={clsx("py-2 px-3", s.volume_ratio > 2 ? "text-amber-600" : "text-gray-500")}>
                  {s.volume_ratio.toFixed(1)}x
                </td>
                {!compact && (
                  <>
                    <td className="py-2 px-3 text-gray-500">{s.analyst_rating || "—"}</td>
                    <td className="py-2 px-3 text-gray-500">{s.price_target ? `$${s.price_target.toFixed(0)}` : "—"}</td>
                    <td className="py-2 px-3 text-gray-500">
                      {s.short_interest_pct != null ? `${(s.short_interest_pct * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-2 px-3">
                      {s.squeeze_score != null ? (
                        <span className={s.squeeze_score > 60 ? "text-red-600" : s.squeeze_score > 30 ? "text-amber-600" : "text-green-600"}>
                          {s.squeeze_score.toFixed(0)}
                        </span>
                      ) : "—"}
                    </td>
                  </>
                )}
                <td className="py-2 px-3">
                  {s.options_unusual ? (
                    <span className="text-amber-600">● Unusual</span>
                  ) : <span className="text-gray-500">—</span>}
                </td>
                <td className="py-2 px-3">
                  <SentimentBadge sentiment={sentiments[s.ticker]} />
                </td>
                {!compact && (
                  <td className="py-2 px-3 text-center">
                    <button
                      onClick={(e) => handleRemove(s.ticker, e)}
                      disabled={removingTicker === s.ticker}
                      className="text-red-600 hover:text-red-800 disabled:text-gray-400 transition-colors"
                      title={`Remove ${s.ticker}`}
                    >
                      {removingTicker === s.ticker ? "..." : "🗑️"}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
