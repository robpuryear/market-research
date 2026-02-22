"use client";

import { useState } from "react";
import { runBacktest, fetchBacktestStrategies } from "@/lib/api";
import type { BacktestConfig, BacktestResult, StrategyInfo } from "@/lib/types";
import useSWR from "swr";

export function useBacktestStrategies() {
  return useSWR<{ strategies: StrategyInfo[] }>(
    "/api/backtest/strategies",
    fetchBacktestStrategies,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );
}

export function useBacktest() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (config: BacktestConfig) => {
    setIsRunning(true);
    setError(null);
    setResult(null);

    try {
      const data = await runBacktest(config);
      setResult(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Backtest failed";
      setError(message);
      throw err;
    } finally {
      setIsRunning(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
    setIsRunning(false);
  };

  return {
    run,
    reset,
    result,
    error,
    isRunning,
  };
}
