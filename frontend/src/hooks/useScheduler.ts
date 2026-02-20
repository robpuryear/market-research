"use client";
import useSWR from "swr";
import { fetchSchedulerStatus } from "@/lib/api";
import { REFRESH_INTERVALS } from "@/lib/constants";

export function useScheduler() {
  return useSWR("scheduler", fetchSchedulerStatus, {
    refreshInterval: REFRESH_INTERVALS.scheduler,
    revalidateOnFocus: false,
  });
}
