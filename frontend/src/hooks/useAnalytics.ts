"use client";
import useSWR from "swr";
import { fetchSqueeze, fetchCorrelation, fetchSignals, fetchEarningsCalendar, fetchCompositeSentiment } from "@/lib/api";

export function useSqueeze() {
  return useSWR("analytics-squeeze", fetchSqueeze, {
    refreshInterval: 600_000,
    revalidateOnFocus: false,
  });
}

export function useCorrelation() {
  return useSWR("analytics-correlation", fetchCorrelation, {
    refreshInterval: 600_000,
    revalidateOnFocus: false,
  });
}

export function useSignals(ticker: string) {
  return useSWR(
    ticker ? `analytics-signals-${ticker}` : null,
    () => fetchSignals(ticker),
    {
      refreshInterval: 600_000,
      revalidateOnFocus: false,
    }
  );
}

export function useEarningsCalendar() {
  return useSWR("earnings-calendar", fetchEarningsCalendar, {
    refreshInterval: 3_600_000,
    revalidateOnFocus: false,
  });
}

export function useCompositeSentiment(ticker: string) {
  return useSWR(
    ticker ? `composite-sentiment-${ticker}` : null,
    () => fetchCompositeSentiment(ticker),
    {
      refreshInterval: 600_000,  // 10 minutes
      revalidateOnFocus: false,
    }
  );
}
