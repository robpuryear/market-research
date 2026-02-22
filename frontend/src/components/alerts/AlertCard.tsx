import type { Alert, PriceCondition, SignalCondition, EarningsCondition } from "@/lib/types";

interface AlertCardProps {
  alert: Alert;
  onToggle: (id: string, enabled: boolean) => void;
  onDelete: (id: string) => void;
}

export function AlertCard({ alert, onToggle, onDelete }: AlertCardProps) {
  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case "price": return "Price";
      case "signal": return "Signal";
      case "earnings": return "Earnings";
      default: return type;
    }
  };

  const getConditionSummary = () => {
    if (alert.alert_type === "price") {
      const cond = alert.condition as PriceCondition;
      if (cond.condition_type === "above") {
        return `Above $${cond.threshold}`;
      } else if (cond.condition_type === "below") {
        return `Below $${cond.threshold}`;
      } else if (cond.condition_type === "pct_change") {
        return `±${cond.percentage}% change`;
      } else if (cond.condition_type === "ma_cross") {
        return `${cond.ma_period}MA cross`;
      }
    } else if (alert.alert_type === "signal") {
      const cond = alert.condition as SignalCondition;
      if (cond.signal_type === "rsi") {
        return `RSI ${cond.operator} ${cond.threshold}`;
      } else if (cond.signal_type === "ml_signal") {
        return `ML signal (${cond.direction || "any"})`;
      }
    } else if (alert.alert_type === "earnings") {
      const cond = alert.condition as EarningsCondition;
      return `${cond.days_before} days before earnings`;
    }

    return "Custom condition";
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className={`border rounded-lg p-4 ${alert.enabled ? "bg-white border-gray-200" : "bg-gray-50 border-gray-300"}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-3 mb-2">
            <span className="text-lg font-bold text-gray-900">{alert.ticker}</span>
            <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-100 text-blue-800">
              {getAlertTypeLabel(alert.alert_type)}
            </span>
            {!alert.enabled && (
              <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-200 text-gray-600">
                Disabled
              </span>
            )}
          </div>

          {/* Condition */}
          <div className="text-sm text-gray-700 mb-2">{getConditionSummary()}</div>

          {/* Custom Message */}
          {alert.message && (
            <div className="text-sm text-gray-600 italic mb-2">&quot;{alert.message}&quot;</div>
          )}

          {/* Stats */}
          <div className="flex gap-4 text-xs text-gray-500 mt-3">
            <div>
              <span className="font-medium">Triggered:</span> {alert.trigger_count}x
            </div>
            {alert.triggered_at && (
              <div>
                <span className="font-medium">Last:</span> {formatDate(alert.triggered_at)}
              </div>
            )}
            {alert.last_checked && (
              <div>
                <span className="font-medium">Checked:</span> {formatDate(alert.last_checked)}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 ml-4">
          <button
            onClick={() => onToggle(alert.id, !alert.enabled)}
            className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
              alert.enabled
                ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                : "bg-green-100 text-green-800 hover:bg-green-200"
            }`}
          >
            {alert.enabled ? "Disable" : "Enable"}
          </button>
          <button
            onClick={() => onDelete(alert.id)}
            className="px-3 py-1 text-sm font-medium rounded bg-red-100 text-red-800 hover:bg-red-200 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
