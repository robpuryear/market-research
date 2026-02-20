"use client";
import useSWR from "swr";
import { fetchReports } from "@/lib/api";
import { REFRESH_INTERVALS } from "@/lib/constants";

export function useReports() {
  return useSWR("reports", fetchReports, {
    refreshInterval: REFRESH_INTERVALS.reports,
    revalidateOnFocus: true,
  });
}
