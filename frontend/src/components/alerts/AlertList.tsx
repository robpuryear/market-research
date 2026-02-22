"use client";

import { AlertCard } from "./AlertCard";
import type { Alert } from "@/lib/types";

interface AlertListProps {
  alerts: Alert[];
  onToggle: (id: string, enabled: boolean) => void;
  onDelete: (id: string) => void;
}

export function AlertList({ alerts, onToggle, onDelete }: AlertListProps) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <div className="text-gray-400 text-lg mb-2">No alerts yet</div>
        <p className="text-gray-500 text-sm">
          Create your first alert to get notified about price movements, signals, or earnings.
        </p>
      </div>
    );
  }

  // Group alerts by enabled status
  const enabledAlerts = alerts.filter(a => a.enabled);
  const disabledAlerts = alerts.filter(a => !a.enabled);

  return (
    <div className="space-y-6">
      {/* Active Alerts */}
      {enabledAlerts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Active Alerts ({enabledAlerts.length})
          </h2>
          <div className="space-y-3">
            {enabledAlerts.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onToggle={onToggle}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      )}

      {/* Disabled Alerts */}
      {disabledAlerts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-600 mb-3">
            Disabled Alerts ({disabledAlerts.length})
          </h2>
          <div className="space-y-3">
            {disabledAlerts.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onToggle={onToggle}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
