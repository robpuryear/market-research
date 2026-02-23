"use client";

import { useParams, useRouter } from "next/navigation";
import { useStrategy, useStrategyResults } from "@/hooks/useStrategies";

export default function StrategyResultsPage() {
  const params = useParams();
  const router = useRouter();
  const strategyId = params.id as string;

  const { strategy, isLoading: strategyLoading } = useStrategy(strategyId);
  const { results, isLoading: resultsLoading } = useStrategyResults(strategyId);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (strategyLoading || resultsLoading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-600 mt-2">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-800">
          Strategy not found
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:text-blue-800 mb-2 text-sm"
        >
          ← Back to Strategies
        </button>
        <h1 className="text-3xl font-bold text-gray-900">{strategy.name}</h1>
        {strategy.description && (
          <p className="text-gray-600 mt-1">{strategy.description}</p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Status</p>
          <p className={`text-lg font-semibold ${strategy.enabled ? "text-green-600" : "text-gray-600"}`}>
            {strategy.enabled ? "Active" : "Disabled"}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Scope</p>
          <p className="text-lg font-semibold text-gray-900 capitalize">{strategy.scope}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Hits Today</p>
          <p className="text-lg font-semibold text-gray-900">{strategy.hits_today}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Hits</p>
          <p className="text-lg font-semibold text-gray-900">{strategy.total_hits}</p>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Match History</h2>
        </div>

        {!results || results.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No matches yet. Run the strategy to see results.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ticker
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Matched At
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Signal Strength
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Conditions
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Indicators
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {results.map((result) => (
                  <tr key={result.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="font-medium text-gray-900">{result.ticker}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(result.matched_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      ${result.current_price.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${result.signal_strength}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">{result.signal_strength.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex gap-2">
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            result.entry_conditions_met
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {result.entry_conditions_met ? "Entry ✓" : "Entry ✗"}
                        </span>
                        {strategy.exit_conditions && (
                          <span
                            className={`px-2 py-1 text-xs rounded ${
                              result.exit_conditions_met
                                ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {result.exit_conditions_met ? "Exit ✓" : "Exit ✗"}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      <div className="space-y-1 max-w-xs">
                        {Object.entries(result.indicator_values).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-medium">{key}:</span>
                            <span>
                              {typeof value === "number" ? value.toFixed(2) : value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
