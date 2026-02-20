"use client";
import useSWR from "swr";
import { fetchWatchlist, fetchStockDetail } from "@/lib/api";
import { REFRESH_INTERVALS } from "@/lib/constants";

export function useWatchlist() {
  return useSWR("watchlist", fetchWatchlist, {
    refreshInterval: REFRESH_INTERVALS.watchlist,
    revalidateOnFocus: false,
  });
}

export function useStockDetail(ticker: string) {
  return useSWR(ticker ? `stock-${ticker}` : null, () => fetchStockDetail(ticker), {
    refreshInterval: REFRESH_INTERVALS.watchlist,
    revalidateOnFocus: false,
  });
}
