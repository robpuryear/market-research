import useSWR from "swr";
import {
  fetchPositions,
  fetchPortfolioMetrics,
  fetchTransactions,
  addPosition as apiAddPosition,
  sellPosition as apiSellPosition,
  updatePosition as apiUpdatePosition,
  deletePosition as apiDeletePosition,
} from "@/lib/api";
import type { Position, PortfolioMetrics, Transaction } from "@/lib/types";

export function usePositions(includeClosed = false) {
  const { data, error, isLoading, mutate } = useSWR(
    ["/api/portfolio/positions", includeClosed],
    () => fetchPositions(includeClosed),
    {
      refreshInterval: 30000, // Refresh every 30 seconds for live prices
    }
  );

  const addPosition = async (positionData: {
    ticker: string;
    quantity: number;
    price: number;
    date: string;
    notes?: string;
  }) => {
    const newPosition = await apiAddPosition(positionData);
    mutate(); // Refresh the list
    return newPosition;
  };

  const sellPosition = async (
    positionId: string,
    saleData: { quantity: number; price: number; date: string; notes?: string }
  ) => {
    const updated = await apiSellPosition(positionId, saleData);
    mutate(); // Refresh the list
    return updated;
  };

  const updatePosition = async (positionId: string, updates: { notes?: string }) => {
    const updated = await apiUpdatePosition(positionId, updates);
    mutate(); // Refresh the list
    return updated;
  };

  const deletePosition = async (positionId: string) => {
    await apiDeletePosition(positionId);
    mutate(); // Refresh the list
  };

  return {
    positions: data,
    error,
    isLoading,
    refresh: mutate,
    addPosition,
    sellPosition,
    updatePosition,
    deletePosition,
  };
}

export function usePortfolioMetrics(cash = 0) {
  const { data, error, isLoading, mutate } = useSWR(
    ["/api/portfolio/metrics", cash],
    () => fetchPortfolioMetrics(cash),
    {
      refreshInterval: 30000, // Refresh every 30 seconds
    }
  );

  return {
    metrics: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useTransactions(positionId?: string) {
  const { data, error, isLoading, mutate } = useSWR(
    ["/api/portfolio/transactions", positionId],
    () => fetchTransactions(positionId),
    {
      refreshInterval: 60000, // Refresh every minute
    }
  );

  return {
    transactions: data,
    error,
    isLoading,
    refresh: mutate,
  };
}
