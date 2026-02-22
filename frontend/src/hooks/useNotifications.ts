import useSWR from "swr";
import { fetchNotifications, markNotificationRead as apiMarkRead } from "@/lib/api";

export function useNotifications(unreadOnly = false) {
  const { data, error, isLoading, mutate } = useSWR(
    ["/api/alerts/notifications", unreadOnly],
    () => fetchNotifications(50, unreadOnly),
    { refreshInterval: 30000 }  // Refresh every 30s
  );

  const markRead = async (notifId: string) => {
    await apiMarkRead(notifId);
    mutate(); // Refresh the list
  };

  const unreadCount = data?.filter(n => !n.read).length || 0;

  return {
    notifications: data,
    error,
    isLoading,
    refresh: mutate,
    markRead,
    unreadCount,
  };
}
