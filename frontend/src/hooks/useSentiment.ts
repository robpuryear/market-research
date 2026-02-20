"use client";
import useSWR from "swr";
import { fetchRedditSentiment, fetchFlowToxicity, fetchStockTwits, fetchNewsSentiment } from "@/lib/api";
import { REFRESH_INTERVALS } from "@/lib/constants";

export function useRedditSentiment() {
  return useSWR("reddit-sentiment", fetchRedditSentiment, {
    refreshInterval: REFRESH_INTERVALS.sentiment,
    revalidateOnFocus: false,
  });
}

export function useFlowToxicity(ticker: string) {
  return useSWR(ticker ? `flow-toxicity-${ticker}` : null, () => fetchFlowToxicity(ticker), {
    refreshInterval: REFRESH_INTERVALS.sentiment,
    revalidateOnFocus: false,
  });
}

export function useStockTwits(ticker: string) {
  return useSWR(ticker ? `stocktwits-${ticker}` : null, () => fetchStockTwits(ticker), {
    refreshInterval: REFRESH_INTERVALS.sentiment,
    revalidateOnFocus: false,
  });
}

export function useNewsSentiment(ticker: string) {
  return useSWR(ticker ? `news-sentiment-${ticker}` : null, () => fetchNewsSentiment(ticker), {
    refreshInterval: REFRESH_INTERVALS.sentiment,
    revalidateOnFocus: false,
  });
}
