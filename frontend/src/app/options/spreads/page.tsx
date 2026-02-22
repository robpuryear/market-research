"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import type { SpreadLeg, SpreadAnalysis } from "@/lib/types";

// Add SpreadAnalysis types if not already in types.ts
interface SpreadRequest {
  ticker: string;
  spot_price: number;
  legs: SpreadLeg[];
  spread_type?: string;
}

export default function SpreadBuilderPage() {
  const [ticker, setTicker] = useState("AAPL");
  const [spotPrice, setSpotPrice] = useState(150);
  const [spreadType, setSpreadType] = useState("bull_call_spread");
  const [analysis, setAnalysis] = useState<SpreadAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Spread configurations
  const [bullCallLong, setBullCallLong] = useState({ strike: 145, price: 8.50 });
  const [bullCallShort, setBullCallShort] = useState({ strike: 155, price: 3.20 });

  const analyzeSpread = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      let legs: SpreadLeg[] = [];

      // Build legs based on spread type
      if (spreadType === "bull_call_spread") {
        legs = [
          {
            strike: bullCallLong.strike,
            contract_type: "call",
            action: "buy",
            quantity: 1,
            price: bullCallLong.price,
            expiration: "2026-03-20",
            delta: null,
          },
          {
            strike: bullCallShort.strike,
            contract_type: "call",
            action: "sell",
            quantity: 1,
            price: bullCallShort.price,
            expiration: "2026-03-20",
            delta: null,
          },
        ];
      }

      const request: SpreadRequest = {
        ticker,
        spot_price: spotPrice,
        legs,
        spread_type: spreadType,
      };

      const result = await apiFetch<SpreadAnalysis>("/api/options/spread/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze spread");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Spread Builder</h1>
          <p className="text-gray-600 mt-1">Build and analyze options spreads with P/L diagrams</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h2>

              {/* Ticker & Spot */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ticker</label>
                  <input
                    type="text"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Spot Price ($)</label>
                  <input
                    type="number"
                    value={spotPrice}
                    onChange={(e) => setSpotPrice(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    step="0.01"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Spread Type</label>
                  <select
                    value={spreadType}
                    onChange={(e) => setSpreadType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="bull_call_spread">Bull Call Spread</option>
                    <option value="bear_put_spread">Bear Put Spread</option>
                    <option value="iron_condor">Iron Condor</option>
                  </select>
                </div>
              </div>

              {/* Leg Configuration */}
              {spreadType === "bull_call_spread" && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Legs</h3>

                  {/* Long Call */}
                  <div className="mb-4 p-3 bg-green-50 rounded">
                    <div className="text-sm font-medium text-green-900 mb-2">Long Call (Buy)</div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Strike</label>
                        <input
                          type="number"
                          value={bullCallLong.strike}
                          onChange={(e) => setBullCallLong({...bullCallLong, strike: Number(e.target.value)})}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                          step="0.5"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Premium</label>
                        <input
                          type="number"
                          value={bullCallLong.price}
                          onChange={(e) => setBullCallLong({...bullCallLong, price: Number(e.target.value)})}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                          step="0.05"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Short Call */}
                  <div className="p-3 bg-red-50 rounded">
                    <div className="text-sm font-medium text-red-900 mb-2">Short Call (Sell)</div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Strike</label>
                        <input
                          type="number"
                          value={bullCallShort.strike}
                          onChange={(e) => setBullCallShort({...bullCallShort, strike: Number(e.target.value)})}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                          step="0.5"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Premium</label>
                        <input
                          type="number"
                          value={bullCallShort.price}
                          onChange={(e) => setBullCallShort({...bullCallShort, price: Number(e.target.value)})}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                          step="0.05"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Analyze Button */}
              <button
                onClick={analyzeSpread}
                disabled={isAnalyzing}
                className="w-full mt-6 bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-medium"
              >
                {isAnalyzing ? "Analyzing..." : "Analyze Spread"}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-800 font-medium">Error:</p>
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            {analysis ? (
              <div className="space-y-6">
                {/* Metrics */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    {analysis.spread_type.replace(/_/g, " ").toUpperCase()}
                  </h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-green-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Max Profit</div>
                      <div className="text-2xl font-bold text-green-600">
                        ${analysis.max_profit.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-red-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Max Loss</div>
                      <div className="text-2xl font-bold text-red-600">
                        ${analysis.max_loss.toFixed(2)}
                      </div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Net Cost</div>
                      <div className={`text-2xl font-bold ${analysis.net_debit_credit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${Math.abs(analysis.net_debit_credit).toFixed(2)}
                        <span className="text-sm ml-1">{analysis.net_debit_credit >= 0 ? 'CR' : 'DR'}</span>
                      </div>
                    </div>
                    <div className="bg-blue-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Risk/Reward</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {analysis.risk_reward_ratio.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {/* Breakevens */}
                  {analysis.breakeven_points.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="text-sm font-medium text-gray-700">Breakeven Points:</div>
                      <div className="flex gap-3 mt-2">
                        {analysis.breakeven_points.map((be, idx) => (
                          <div key={idx} className="px-3 py-1 bg-yellow-100 text-yellow-900 rounded font-mono text-sm">
                            ${be.toFixed(2)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* P/L Diagram */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">P/L at Expiration</h2>
                  <div className="relative h-96">
                    <svg className="w-full h-full" viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet">
                      {/* Grid */}
                      <line x1="50" y1="200" x2="750" y2="200" stroke="#e5e7eb" strokeWidth="2" />
                      <line x1="400" y1="20" x2="400" y2="380" stroke="#e5e7eb" strokeWidth="1" strokeDasharray="5,5" />

                      {/* P/L Line */}
                      <polyline
                        points={analysis.price_points.map((price, i) => {
                          const x = 50 + ((price - analysis.price_points[0]) / (analysis.price_points[analysis.price_points.length - 1] - analysis.price_points[0])) * 700;
                          const y = 200 - (analysis.pnl_at_expiration[i] / Math.max(Math.abs(analysis.max_profit), Math.abs(analysis.max_loss))) * 150;
                          return `${x},${y}`;
                        }).join(" ")}
                        fill="none"
                        stroke="#2563eb"
                        strokeWidth="3"
                      />

                      {/* Spot Price Line */}
                      {(() => {
                        const spotX = 50 + ((analysis.spot_price - analysis.price_points[0]) / (analysis.price_points[analysis.price_points.length - 1] - analysis.price_points[0])) * 700;
                        return <line x1={spotX} y1="20" x2={spotX} y2="380" stroke="#10b981" strokeWidth="2" strokeDasharray="5,5" />;
                      })()}

                      {/* Labels */}
                      <text x="400" y="15" textAnchor="middle" className="text-xs fill-gray-600">Stock Price at Expiration</text>
                      <text x="30" y="205" textAnchor="end" className="text-xs fill-gray-600">$0</text>
                      <text x="30" y="50" textAnchor="end" className="text-xs fill-green-600">Profit</text>
                      <text x="30" y="360" textAnchor="end" className="text-xs fill-red-600">Loss</text>
                    </svg>
                  </div>
                  <div className="flex items-center justify-center gap-6 mt-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-0.5 bg-blue-600"></div>
                      <span className="text-gray-600">P/L Curve</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-0.5 bg-green-500 border-dashed"></div>
                      <span className="text-gray-600">Current Spot (${analysis.spot_price.toFixed(2)})</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <div className="text-gray-400 text-lg">
                  Configure your spread and click "Analyze Spread" to see results
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
