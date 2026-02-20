"use client";
import { useState } from "react";
import { fetchMarketScan, addToWatchlist } from "@/lib/api";
import type { ScanCandidate } from "@/lib/types";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { mutate } from "swr";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

export default function ScannerPage() {
  const [isScanning, setIsScanning] = useState(false);
  const [candidates, setCandidates] = useState<ScanCandidate[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [universe, setUniverse] = useState("top100");
  const [topN, setTopN] = useState(10);
  const [minScore, setMinScore] = useState(0);
  const [addingTicker, setAddingTicker] = useState<string | null>(null);
  const [addedTickers, setAddedTickers] = useState<Set<string>>(new Set());

  const handleScan = async () => {
    setIsScanning(true);
    setError(null);
    setCandidates(null);  // Clear previous results
    console.log("🔍 Starting market scan...");
    try {
      const results = await fetchMarketScan({
        universe,
        limit: universe === "all" ? 50 : 30,  // Reduced for faster scanning
        min_price: 5.0,
        max_price: 1000.0,
        min_composite: minScore,
        top_n: topN,
      });
      console.log("✅ Scan complete! Results:", results);
      console.log(`Found ${results.length} candidates`);
      setCandidates(results);
    } catch (err: any) {
      console.error("❌ Scan failed:", err);
      setError(err.message || "Failed to scan market");
    } finally {
      setIsScanning(false);
    }
  };

  const handleAddToWatchlist = async (ticker: string) => {
    setAddingTicker(ticker);
    try {
      await addToWatchlist(ticker);
      setAddedTickers(prev => new Set(prev).add(ticker));
      mutate("watchlist"); // Refresh watchlist
      setTimeout(() => {
        setAddedTickers(prev => {
          const next = new Set(prev);
          next.delete(ticker);
          return next;
        });
      }, 3000); // Show "Added!" for 3 seconds
    } catch (err: any) {
      if (err.message.includes("409")) {
        alert(`${ticker} is already in your watchlist`);
      } else {
        alert(`Failed to add ${ticker}: ${err.message}`);
      }
    } finally {
      setAddingTicker(null);
    }
  };

  const renderScoreBar = (score: number, label: string, tooltip?: string) => {
    const color =
      score >= 70 ? "bg-green-500" : score >= 40 ? "bg-yellow-500" : "bg-red-500";
    return (
      <div className="flex items-center gap-2 text-xs">
        <span className="w-32 text-gray-600 flex items-center gap-1">
          {label}:
          {tooltip && <InfoIcon tooltip={tooltip} />}
        </span>
        <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
          <div className={`h-full ${color}`} style={{ width: `${score}%` }} />
        </div>
        <span className="w-10 text-right font-mono text-gray-700">{score.toFixed(0)}</span>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">
          🔍 Market Scanner
        </h1>
        <div className="text-xs text-gray-500">Find top stock opportunities</div>
      </div>

      {/* Controls */}
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Universe
            </label>
            <select
              value={universe}
              onChange={(e) => setUniverse(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="top100">Top 100 (S&P 500 leaders)</option>
              <option value="momentum">High Momentum</option>
              <option value="small_mid">Small/Mid Cap</option>
              <option value="all">All Universes (~200 stocks)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Top Results
            </label>
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Min Score
            </label>
            <select
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>0 (Show All)</option>
              <option value={20}>20+</option>
              <option value={30}>30+</option>
              <option value={40}>40+</option>
              <option value={50}>50+</option>
              <option value={60}>60+</option>
            </select>
          </div>

          <button
            onClick={handleScan}
            disabled={isScanning}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm font-medium rounded transition-colors"
          >
            {isScanning ? "Scanning..." : "Scan Now"}
          </button>
        </div>

        {isScanning && (
          <div className="mt-4 text-sm text-gray-600">
            <LoadingSpinner />
            <div className="mt-2">
              Scanning {universe === "all" ? "50" : "30"} stocks. This may take 15-30
              seconds...
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded px-4 py-3">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {candidates && candidates.length > 0 && (
        <div className="space-y-4">
          <div className="text-sm font-medium text-gray-700">
            Found {candidates.length} top opportunities (sorted by composite score)
          </div>

          {candidates.map((c, idx) => (
            <div
              key={c.ticker}
              className="bg-white border border-gray-300 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-300 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="font-bold text-lg text-gray-900">{c.ticker}</div>
                    <div className="text-xs text-gray-600">{c.company_name}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleAddToWatchlist(c.ticker)}
                    disabled={addingTicker === c.ticker || addedTickers.has(c.ticker)}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-xs font-medium rounded transition-colors"
                  >
                    {addingTicker === c.ticker
                      ? "Adding..."
                      : addedTickers.has(c.ticker)
                        ? "✓ Added!"
                        : "+ Add to Watchlist"}
                  </button>
                  <div className="flex items-center gap-1">
                    <div className="bg-green-500 text-white px-4 py-2 rounded-full text-lg font-bold">
                      {c.composite_score.toFixed(0)}
                    </div>
                    <InfoIcon tooltip={TOOLTIPS.compositeScore} className="text-gray-700" />
                  </div>
                </div>
              </div>

              {/* Body */}
              <div className="p-4 space-y-4">
                {/* Info Grid */}
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-xs text-gray-500">Price</div>
                    <div className="font-semibold text-gray-800">${c.price.toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 flex items-center gap-1">
                      Volume Ratio <InfoIcon tooltip={TOOLTIPS.volumeRatio} />
                    </div>
                    <div className="font-semibold text-gray-800">
                      {c.volume_ratio.toFixed(1)}x
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 flex items-center gap-1">
                      Market Cap <InfoIcon tooltip={TOOLTIPS.marketCap} />
                    </div>
                    <div className="font-semibold text-gray-800">
                      {c.market_cap ? `$${(c.market_cap / 1e9).toFixed(1)}B` : "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">Sector</div>
                    <div className="font-semibold text-gray-800">{c.sector || "—"}</div>
                  </div>
                </div>

                {/* Scores */}
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-700 flex items-center gap-1">
                    Opportunity Scores <InfoIcon tooltip={TOOLTIPS.compositeScore} />
                  </div>
                  {renderScoreBar(c.squeeze_score, "Squeeze Potential", TOOLTIPS.squeezeScore)}
                  {renderScoreBar(
                    Math.min(c.bullish_signal_count * 25, 100),
                    "Technical Signals",
                    "Number of bullish ML signals detected (RSI divergence, MACD cross, etc.)"
                  )}
                  {renderScoreBar(
                    Math.min(c.unusual_options_count * 20, 100),
                    "Options Activity",
                    TOOLTIPS.unusualOptions
                  )}
                  {renderScoreBar(c.iv_rank, "IV Rank", TOOLTIPS.ivRank)}
                </div>

                {/* Signals */}
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    ML Signals ({c.bullish_signal_count} Bullish, {c.bearish_signal_count}{" "}
                    Bearish)
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {c.ml_signals.length === 0 ? (
                      <span className="text-xs text-gray-500 px-3 py-1 bg-gray-100 rounded-full">
                        No signals
                      </span>
                    ) : (
                      c.ml_signals.slice(0, 5).map((sig, i) => (
                        <span
                          key={i}
                          className={`text-xs px-3 py-1 rounded-full font-medium ${
                            sig.direction === "bullish"
                              ? "bg-green-100 text-green-800"
                              : sig.direction === "bearish"
                                ? "bg-red-100 text-red-800"
                                : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {sig.signal_type}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                {/* Highlights */}
                <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-200">
                  {c.squeeze_score > 70 && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-3 py-1 rounded font-medium">
                      🔥 High Squeeze Score
                    </span>
                  )}
                  {c.unusual_options_count > 0 && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-3 py-1 rounded font-medium">
                      📈 Unusual Options
                    </span>
                  )}
                  {c.iv_rank > 80 && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-3 py-1 rounded font-medium">
                      ⚡ High IV
                    </span>
                  )}
                  {c.volume_ratio > 2 && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-3 py-1 rounded font-medium">
                      📊 High Volume
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {candidates && candidates.length === 0 && (
        <div className="bg-white border border-gray-300 rounded-lg p-8 text-center text-gray-500">
          No candidates found meeting the criteria. Try adjusting filters.
        </div>
      )}
    </div>
  );
}
