"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetchOptionsChain, fetchOptionsExpirations, fetchOptionsAnalytics } from "@/lib/api";
import type { OptionsChain, ExpirationDate, OptionsAnalytics } from "@/lib/types";

export default function OptionsPage() {
  const [ticker, setTicker] = useState("AAPL");
  const [selectedExp, setSelectedExp] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("AAPL");

  // Fetch expirations
  const { data: expirations } = useSWR<ExpirationDate[]>(
    ticker ? `/api/options/expirations/${ticker}` : null,
    () => fetchOptionsExpirations(ticker)
  );

  // Fetch chain for selected expiration
  const { data: chain, isLoading: chainLoading } = useSWR<OptionsChain>(
    ticker && selectedExp ? `/api/options/chain/${ticker}/${selectedExp}` : null,
    () => fetchOptionsChain(ticker, selectedExp!)
  );

  // Fetch analytics
  const { data: analytics } = useSWR<OptionsAnalytics>(
    ticker ? `/api/options/analytics/${ticker}` : null,
    () => fetchOptionsAnalytics(ticker)
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setTicker(searchInput.toUpperCase());
    setSelectedExp(null);
  };

  // Auto-select first expiration
  if (expirations && !selectedExp && expirations.length > 0) {
    setSelectedExp(expirations[0].date);
  }

  const formatPercent = (val: number | null) =>
    val !== null ? `${(val * 100).toFixed(2)}%` : "—";
  const formatNumber = (val: number | null, decimals = 2) =>
    val !== null ? val.toFixed(decimals) : "—";

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Options Chain</h1>
          <p className="text-gray-600 mt-1">View options contracts with Greeks and analytics</p>
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <form onSubmit={handleSearch} className="flex gap-3">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
              placeholder="Enter ticker..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              Load Chain
            </button>
          </form>
        </div>

        {/* Analytics Summary */}
        {analytics && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {ticker} @ ${analytics.spot_price.toFixed(2)}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-sm text-gray-600">Current IV</div>
                <div className="text-lg font-semibold">{formatPercent(analytics.current_iv)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">30D HV</div>
                <div className="text-lg font-semibold">{formatPercent(analytics.hv_30day)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">P/C Ratio</div>
                <div className="text-lg font-semibold">{formatNumber(analytics.put_call_ratio, 2)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">IV Rank</div>
                <div className="text-lg font-semibold">{analytics.iv_rank ? analytics.iv_rank.toFixed(0) : "—"}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">DTE</div>
                <div className="text-lg font-semibold">{analytics.days_to_expiration || "—"}</div>
              </div>
            </div>
          </div>
        )}

        {/* Expiration Selector */}
        {expirations && expirations.length > 0 && (
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="flex items-center gap-3 overflow-x-auto">
              <span className="text-sm font-medium text-gray-700 whitespace-nowrap">Expiration:</span>
              {expirations.slice(0, 10).map((exp) => (
                <button
                  key={exp.date}
                  onClick={() => setSelectedExp(exp.date)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                    selectedExp === exp.date
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {exp.date} ({exp.days_until}d)
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Options Chain */}
        {chainLoading && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-600">Loading options chain...</div>
          </div>
        )}

        {chain && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {chain.ticker} - {chain.expiration} (Spot: ${chain.spot_price.toFixed(2)})
              </h2>
              <div className="text-sm text-gray-600 mt-1">
                Call Vol: {chain.total_call_volume.toLocaleString()} | Put Vol: {chain.total_put_volume.toLocaleString()} | P/C: {formatNumber(chain.put_call_volume_ratio, 2)}
              </div>
            </div>

            <div className="grid grid-cols-2 divide-x divide-gray-200">
              {/* Calls */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-green-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-green-900">Strike</th>
                      <th className="px-3 py-2 text-right font-semibold text-green-900">Last</th>
                      <th className="px-3 py-2 text-right font-semibold text-green-900">Bid/Ask</th>
                      <th className="px-3 py-2 text-right font-semibold text-green-900">Vol</th>
                      <th className="px-3 py-2 text-right font-semibold text-green-900">OI</th>
                      <th className="px-3 py-2 text-right font-semibold text-green-900">IV</th>
                      <th className="px-3 py-2 text-right font-semibold text-green-900">Δ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {chain.calls.map((call) => (
                      <tr key={call.symbol} className={call.moneyness === "ATM" ? "bg-yellow-50" : call.in_the_money ? "bg-green-50" : ""}>
                        <td className="px-3 py-2 font-medium">{call.strike.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">{formatNumber(call.last)}</td>
                        <td className="px-3 py-2 text-right text-xs">{formatNumber(call.bid)}/{formatNumber(call.ask)}</td>
                        <td className="px-3 py-2 text-right">{call.volume.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right">{call.open_interest.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right">{formatPercent(call.implied_volatility)}</td>
                        <td className="px-3 py-2 text-right">{formatNumber(call.delta, 3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Puts */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-red-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-red-900">Strike</th>
                      <th className="px-3 py-2 text-right font-semibold text-red-900">Last</th>
                      <th className="px-3 py-2 text-right font-semibold text-red-900">Bid/Ask</th>
                      <th className="px-3 py-2 text-right font-semibold text-red-900">Vol</th>
                      <th className="px-3 py-2 text-right font-semibold text-red-900">OI</th>
                      <th className="px-3 py-2 text-right font-semibold text-red-900">IV</th>
                      <th className="px-3 py-2 text-right font-semibold text-red-900">Δ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {chain.puts.map((put) => (
                      <tr key={put.symbol} className={put.moneyness === "ATM" ? "bg-yellow-50" : put.in_the_money ? "bg-red-50" : ""}>
                        <td className="px-3 py-2 font-medium">{put.strike.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">{formatNumber(put.last)}</td>
                        <td className="px-3 py-2 text-right text-xs">{formatNumber(put.bid)}/{formatNumber(put.ask)}</td>
                        <td className="px-3 py-2 text-right">{put.volume.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right">{put.open_interest.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right">{formatPercent(put.implied_volatility)}</td>
                        <td className="px-3 py-2 text-right">{formatNumber(put.delta, 3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {!chain && !chainLoading && ticker && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-600">Select an expiration date to view the options chain</div>
          </div>
        )}
      </div>
    </div>
  );
}
