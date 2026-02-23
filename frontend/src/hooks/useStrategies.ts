import useSWR from "swr";
import {
  fetchStrategies,
  fetchStrategy,
  createStrategy as apiCreateStrategy,
  updateStrategy as apiUpdateStrategy,
  deleteStrategy as apiDeleteStrategy,
  runStrategy as apiRunStrategy,
  fetchStrategyResults,
  fetchRecentStrategyResults,
} from "@/lib/api";
import type { Strategy, StrategyResult, ConditionGroup } from "@/lib/types";

export function useStrategies() {
  const { data, error, isLoading, mutate } = useSWR("/api/strategies", fetchStrategies, {
    refreshInterval: 60000, // Refresh every minute
  });

  const createStrategy = async (strategyData: {
    name: string;
    description?: string;
    entry_conditions: ConditionGroup;
    exit_conditions?: ConditionGroup;
    enabled?: boolean;
    scope?: "watchlist" | "market";
    generate_alerts?: boolean;
  }) => {
    const newStrategy = await apiCreateStrategy(strategyData);
    mutate(); // Refresh the list
    return newStrategy;
  };

  const updateStrategy = async (strategyId: string, updates: Partial<Strategy>) => {
    const updated = await apiUpdateStrategy(strategyId, updates);
    mutate(); // Refresh the list
    return updated;
  };

  const deleteStrategy = async (strategyId: string) => {
    await apiDeleteStrategy(strategyId);
    mutate(); // Refresh the list
  };

  const runStrategy = async (strategyId: string) => {
    const results = await apiRunStrategy(strategyId);
    mutate(); // Refresh to update last_run and hit counts
    return results;
  };

  const toggleStrategy = async (strategyId: string, enabled: boolean) => {
    return updateStrategy(strategyId, { enabled });
  };

  return {
    strategies: data,
    error,
    isLoading,
    refresh: mutate,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    runStrategy,
    toggleStrategy,
  };
}

export function useStrategy(strategyId: string) {
  const { data, error, isLoading, mutate } = useSWR(
    strategyId ? `/api/strategies/${strategyId}` : null,
    () => fetchStrategy(strategyId)
  );

  return {
    strategy: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useStrategyResults(strategyId: string, limit = 100) {
  const { data, error, isLoading } = useSWR(
    strategyId ? `/api/strategies/${strategyId}/results` : null,
    () => fetchStrategyResults(strategyId, limit),
    {
      refreshInterval: 30000, // Refresh every 30 seconds
    }
  );

  return {
    results: data,
    error,
    isLoading,
  };
}

export function useRecentStrategyResults(limit = 50) {
  const { data, error, isLoading } = useSWR(
    "/api/strategies/results/recent",
    () => fetchRecentStrategyResults(limit),
    {
      refreshInterval: 30000, // Refresh every 30 seconds
    }
  );

  return {
    results: data,
    error,
    isLoading,
  };
}
