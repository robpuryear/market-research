import useSWR from "swr";
import { fetchAlerts, createAlert as apiCreateAlert, updateAlert as apiUpdateAlert, deleteAlert as apiDeleteAlert } from "@/lib/api";
import type { Alert } from "@/lib/types";

export function useAlerts() {
  const { data, error, isLoading, mutate } = useSWR("/api/alerts", fetchAlerts, {
    refreshInterval: 60000, // Refresh every minute
  });

  const createAlert = async (alertData: {
    ticker: string;
    alert_type: string;
    condition: any;
    notification_methods?: string[];
    message?: string;
  }) => {
    const newAlert = await apiCreateAlert(alertData);
    mutate(); // Refresh the list
    return newAlert;
  };

  const updateAlert = async (alertId: string, updates: Partial<Alert>) => {
    const updated = await apiUpdateAlert(alertId, updates);
    mutate(); // Refresh the list
    return updated;
  };

  const deleteAlert = async (alertId: string) => {
    await apiDeleteAlert(alertId);
    mutate(); // Refresh the list
  };

  const toggleAlert = async (alertId: string, enabled: boolean) => {
    return updateAlert(alertId, { enabled });
  };

  return {
    alerts: data,
    error,
    isLoading,
    refresh: mutate,
    createAlert,
    updateAlert,
    deleteAlert,
    toggleAlert,
  };
}
