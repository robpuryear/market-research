"use client";
import useSWR from "swr";
import { fetchSnapshot, fetchSectors, fetchTechnicals, fetchBreadth, fetchIV, fetchOptions } from "@/lib/api";
import { REFRESH_INTERVALS } from "@/lib/constants";

export function useMarketSnapshot() {
  return useSWR("market-snapshot", fetchSnapshot, {
    refreshInterval: REFRESH_INTERVALS.market,
    revalidateOnFocus: false,
  });
}

export function useSectors() {
  return useSWR("sectors", fetchSectors, {
    refreshInterval: REFRESH_INTERVALS.market,
    revalidateOnFocus: false,
  });
}

export function useTechnicals(ticker: string) {
  return useSWR(ticker ? `technicals-${ticker}` : null, () => fetchTechnicals(ticker), {
    refreshInterval: REFRESH_INTERVALS.market,
    revalidateOnFocus: false,
  });
}

export function useBreadth() {
  return useSWR("breadth", fetchBreadth, {
    refreshInterval: 600_000,
    revalidateOnFocus: false,
  });
}

export function useIV(ticker: string) {
  return useSWR(ticker ? `iv-${ticker}` : null, () => fetchIV(ticker), {
    refreshInterval: 600_000,
    revalidateOnFocus: false,
  });
}

export function useOptions(ticker: string) {
  return useSWR(ticker ? `options-${ticker}` : null, () => fetchOptions(ticker), {
    refreshInterval: 600_000,
    revalidateOnFocus: false,
  });
}
