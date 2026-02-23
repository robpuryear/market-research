"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useStrategies, useRecentStrategyResults } from "@/hooks/useStrategies";
import { StrategyCard } from "@/components/strategies/StrategyCard";
import { StrategyBuilderModal } from "@/components/strategies/StrategyBuilderModal";
import type { ConditionGroup } from "@/lib/types";

export default function StrategiesPage() {
  const router = useRouter();
  const [modalOpen, setModalOpen] = useState(false);
  const { strategies, isLoading, error, createStrategy, runStrategy, toggleStrategy, deleteStrategy } = useStrategies();
  const { results: recentResults } = useRecentStrategyResults(10);

  const handleCreateStrategy = async (strategyData: {
    name: string;
    description?: string;
    entry_conditions: ConditionGroup;
    exit_conditions?: ConditionGroup;
    enabled?: boolean;
    scope?: "watchlist" | "market";
    generate_alerts?: boolean;
  }) => {
    try {
      await createStrategy(strategyData);
      setModalOpen(false);
    } catch (err) {
      console.error("Failed to create strategy:", err);
      alert("Failed to create strategy. Check console for details.");
    }
  };

  const handleRunStrategy = async (id: string) => {
    try {
      const results = await runStrategy(id);
      alert(`Strategy completed! Found ${results.length} matches.`);
    } catch (err) {
      console.error("Failed to run strategy:", err);
      alert("Failed to run strategy. Check console for details.");
    }
  };

  const handleToggleStrategy = async (id: string, enabled: boolean) => {
    try {
      await toggleStrategy(id, enabled);
    } catch (err) {
      console.error("Failed to toggle strategy:", err);
      alert("Failed to toggle strategy. Check console for details.");
    }
  };

  const handleDeleteStrategy = async (id: string) => {
    try {
      await deleteStrategy(id);
    } catch (err) {
      console.error("Failed to delete strategy:", err);
      alert("Failed to delete strategy. Check console for details.");
    }
  };

  const handleViewResults = (id: string) => {
    router.push(`/strategies/${id}/results`);
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-800">
          Error loading strategies: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Strategies</h1>
          <p className="text-gray-600 mt-1">
            Create custom trading strategies with technical indicators
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          + Create Strategy
        </button>
      </div>

      {/* Recent Hits */}
      {recentResults && recentResults.length > 0 && (
        <div className="mb-6 bg-blue-50 rounded-lg border border-blue-200 p-4">
          <h2 className="text-lg font-semibold text-blue-900 mb-3">Recent Hits</h2>
          <div className="space-y-2">
            {recentResults.map((result) => {
              const strategy = strategies?.find((s) => s.id === result.strategy_id);
              return (
                <div
                  key={result.id}
                  className="flex items-center justify-between bg-white rounded p-3 text-sm"
                >
                  <div>
                    <span className="font-medium text-gray-900">{result.ticker}</span>
                    <span className="text-gray-500 mx-2">•</span>
                    <span className="text-gray-600">{strategy?.name || "Unknown Strategy"}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-gray-900">${result.current_price.toFixed(2)}</p>
                      <p className="text-xs text-gray-500">
                        Signal: {result.signal_strength.toFixed(0)}%
                      </p>
                    </div>
                    <button
                      onClick={() => handleViewResults(result.strategy_id)}
                      className="text-blue-600 hover:text-blue-800 text-xs"
                    >
                      View →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Strategies List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-600 mt-2">Loading strategies...</p>
        </div>
      ) : !strategies || strategies.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600 mb-4">No strategies yet</p>
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Create Your First Strategy
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {strategies.map((strategy) => (
            <StrategyCard
              key={strategy.id}
              strategy={strategy}
              onRun={handleRunStrategy}
              onToggle={handleToggleStrategy}
              onDelete={handleDeleteStrategy}
              onViewResults={handleViewResults}
            />
          ))}
        </div>
      )}

      {/* Create Strategy Modal */}
      <StrategyBuilderModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreateStrategy}
      />
    </div>
  );
}
