"use client";

import { useState } from "react";
import { useBacktest, useBacktestStrategies } from "@/hooks/useBacktest";
import type { BacktestConfig } from "@/lib/types";

export default function BacktestPage() {
  const { data: strategiesData, isLoading: strategiesLoading } = useBacktestStrategies();
  const { run, result, error, isRunning, reset } = useBacktest();

  // Form state
  const [config, setConfig] = useState<BacktestConfig>({
    strategy_type: "buy_hold",
    ticker: "AAPL",
    start_date: "2023-01-01",
    end_date: "2024-01-01",
    initial_capital: 100000,
    position_size: 1.0,
    commission: 0.001,
    slippage: 0.001,
    stop_loss: null,
    take_profit: null,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await run(config);
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatNumber = (value: number) => value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Strategy Backtesting</h1>
          <p className="text-gray-600 mt-1">Test trading strategies on historical data</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Strategy Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Strategy
                  </label>
                  <select
                    value={config.strategy_type}
                    onChange={(e) => setConfig({ ...config, strategy_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {strategiesLoading ? (
                      <option>Loading...</option>
                    ) : (
                      strategiesData?.strategies.map((s) => (
                        <option key={s.name} value={s.name}>
                          {s.display_name}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                {/* Ticker */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ticker
                  </label>
                  <input
                    type="text"
                    value={config.ticker}
                    onChange={(e) => setConfig({ ...config, ticker: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="AAPL"
                  />
                </div>

                {/* Date Range */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={config.start_date}
                      onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={config.end_date}
                      onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Initial Capital */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Initial Capital ($)
                  </label>
                  <input
                    type="number"
                    value={config.initial_capital}
                    onChange={(e) => setConfig({ ...config, initial_capital: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1000"
                    step="1000"
                  />
                </div>

                {/* Position Size */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Position Size (0-1)
                  </label>
                  <input
                    type="number"
                    value={config.position_size}
                    onChange={(e) => setConfig({ ...config, position_size: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0.1"
                    max="1"
                    step="0.1"
                  />
                </div>

                {/* Stop Loss / Take Profit */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Stop Loss %
                    </label>
                    <input
                      type="number"
                      value={config.stop_loss || ""}
                      onChange={(e) => setConfig({ ...config, stop_loss: e.target.value ? Number(e.target.value) : null })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Optional"
                      min="0.01"
                      max="1"
                      step="0.01"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Take Profit %
                    </label>
                    <input
                      type="number"
                      value={config.take_profit || ""}
                      onChange={(e) => setConfig({ ...config, take_profit: e.target.value ? Number(e.target.value) : null })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Optional"
                      min="0.01"
                      max="5"
                      step="0.01"
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={isRunning}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {isRunning ? "Running..." : "Run Backtest"}
                  </button>
                  {result && (
                    <button
                      type="button"
                      onClick={reset}
                      className="w-full mt-2 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
                    >
                      Reset
                    </button>
                  )}
                </div>
              </form>
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

            {result ? (
              <div className="space-y-6">
                {/* Performance Metrics */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Final Value</div>
                      <div className="text-2xl font-bold text-gray-900">
                        ${formatNumber(result.final_value)}
                      </div>
                      <div className={`text-sm ${result.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(result.total_return)}
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Total Trades</div>
                      <div className="text-2xl font-bold text-gray-900">{result.total_trades}</div>
                      <div className="text-sm text-gray-600">
                        Win Rate: {formatPercent(result.win_rate)}
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Sharpe Ratio</div>
                      <div className="text-2xl font-bold text-gray-900">
                        {result.sharpe_ratio.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Volatility: {formatPercent(result.volatility)}
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-600">Max Drawdown</div>
                      <div className="text-2xl font-bold text-red-600">
                        {formatPercent(result.max_drawdown)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Annual: {formatPercent(result.annual_return)}
                      </div>
                    </div>
                  </div>

                  {/* Benchmark Comparison */}
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-gray-600">Benchmark (Buy & Hold)</div>
                        <div className="text-lg font-semibold text-gray-900">
                          {formatPercent(result.benchmark_return)}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Alpha</div>
                        <div className={`text-lg font-semibold ${result.alpha >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatPercent(result.alpha)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Trades Table */}
                {result.trades.length > 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                      Trade History ({result.total_trades} trades)
                    </h2>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 border-b border-gray-200">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium text-gray-700">Entry</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-700">Exit</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-700">P&L</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-700">Return</th>
                            <th className="px-4 py-2 text-right font-medium text-gray-700">Days</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-700">Reason</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {result.trades.map((trade, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-4 py-2">{trade.entry_date}</td>
                              <td className="px-4 py-2">{trade.exit_date}</td>
                              <td className={`px-4 py-2 text-right font-medium ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                ${formatNumber(trade.pnl)}
                              </td>
                              <td className={`px-4 py-2 text-right ${trade.return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatPercent(trade.return_pct)}
                              </td>
                              <td className="px-4 py-2 text-right">{trade.hold_days}</td>
                              <td className="px-4 py-2 text-xs text-gray-600">{trade.exit_reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* No Trades Message */}
                {result.trades.length === 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <div className="text-center text-gray-600">
                      <p className="text-lg font-medium">No Trades Executed</p>
                      <p className="text-sm mt-1">
                        The strategy conditions were not met during this period.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <div className="text-gray-400 text-lg">
                  Configure parameters and run a backtest to see results
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
