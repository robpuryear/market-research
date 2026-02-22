"use client";

import { useState } from "react";
import { useAlerts } from "@/hooks/useAlerts";
import { useNotifications } from "@/hooks/useNotifications";
import { AlertList } from "@/components/alerts/AlertList";
import { CreateAlertModal } from "@/components/alerts/CreateAlertModal";
import { NotificationBanner } from "@/components/alerts/NotificationBanner";
import type { PriceCondition, SignalCondition, EarningsCondition } from "@/lib/types";

export default function AlertsPage() {
  const { alerts, isLoading, createAlert, toggleAlert, deleteAlert } = useAlerts();
  const { notifications } = useNotifications(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [visibleNotifications, setVisibleNotifications] = useState<string[]>([]);

  // Show new notifications as they come in
  const latestNotif = notifications?.[0];
  if (latestNotif && !latestNotif.read && !visibleNotifications.includes(latestNotif.id)) {
    setVisibleNotifications([latestNotif.id, ...visibleNotifications]);
  }

  const handleCreateAlert = async (alertData: {
    ticker: string;
    alert_type: string;
    condition: PriceCondition | SignalCondition | EarningsCondition;
    notification_methods: string[];
    message?: string;
  }) => {
    try {
      await createAlert(alertData);
    } catch (error) {
      console.error("Failed to create alert:", error);
      alert("Failed to create alert. Please try again.");
    }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await toggleAlert(id, enabled);
    } catch (error) {
      console.error("Failed to toggle alert:", error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this alert?")) return;

    try {
      await deleteAlert(id);
    } catch (error) {
      console.error("Failed to delete alert:", error);
    }
  };

  const handleDismissNotification = (id: string) => {
    setVisibleNotifications(visibleNotifications.filter(nid => nid !== id));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Alerts</h1>
            <p className="text-gray-600 mt-1">
              Get notified about price movements, signals, and earnings
            </p>
          </div>
          <button
            onClick={() => setModalOpen(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            + Create Alert
          </button>
        </div>

        {/* Recent Notifications */}
        {notifications && notifications.length > 0 && (
          <div className="mb-6 bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Recent Notifications
            </h2>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {notifications.slice(0, 10).map(notif => (
                <div
                  key={notif.id}
                  className={`flex items-start gap-3 p-3 rounded ${
                    notif.read ? "bg-gray-50" : "bg-blue-50"
                  }`}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm">{notif.ticker}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(notif.triggered_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{notif.message}</p>
                  </div>
                  {!notif.read && (
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-1"></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Alerts List */}
        {isLoading ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-gray-600">Loading alerts...</div>
          </div>
        ) : (
          <AlertList
            alerts={alerts || []}
            onToggle={handleToggle}
            onDelete={handleDelete}
          />
        )}

        {/* Create Alert Modal */}
        <CreateAlertModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          onCreate={handleCreateAlert}
        />

        {/* Toast Notifications */}
        {notifications &&
          visibleNotifications.map(nid => {
            const notif = notifications.find(n => n.id === nid);
            if (!notif) return null;
            return (
              <NotificationBanner
                key={notif.id}
                notification={notif}
                onDismiss={handleDismissNotification}
                autoHideDuration={5000}
              />
            );
          })}
      </div>
    </div>
  );
}
