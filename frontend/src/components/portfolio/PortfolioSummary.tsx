import type { PortfolioMetrics } from "@/lib/types";

interface PortfolioSummaryProps {
  metrics: PortfolioMetrics;
}

export function PortfolioSummary({ metrics }: PortfolioSummaryProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const getColorClass = (value: number) => {
    if (value > 0) return "text-green-600";
    if (value < 0) return "text-red-600";
    return "text-gray-600";
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Value */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Total Value</div>
        <div className="text-2xl font-bold text-gray-900">
          {formatCurrency(metrics.total_value)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Cash: {formatCurrency(metrics.cash)}
        </div>
      </div>

      {/* Total P&L */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Total P&L</div>
        <div className={`text-2xl font-bold ${getColorClass(metrics.total_pnl)}`}>
          {formatCurrency(metrics.total_pnl)}
        </div>
        <div className={`text-xs font-medium mt-1 ${getColorClass(metrics.total_return_pct)}`}>
          {formatPercent(metrics.total_return_pct)}
        </div>
      </div>

      {/* Unrealized P&L */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Unrealized P&L</div>
        <div className={`text-2xl font-bold ${getColorClass(metrics.unrealized_pnl)}`}>
          {formatCurrency(metrics.unrealized_pnl)}
        </div>
        <div className={`text-xs font-medium mt-1 ${getColorClass(metrics.unrealized_pnl_pct)}`}>
          {formatPercent(metrics.unrealized_pnl_pct)}
        </div>
      </div>

      {/* Realized P&L */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Realized P&L</div>
        <div className={`text-2xl font-bold ${getColorClass(metrics.realized_pnl)}`}>
          {formatCurrency(metrics.realized_pnl)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Closed positions
        </div>
      </div>

      {/* Win Rate */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Win Rate</div>
        <div className="text-2xl font-bold text-gray-900">
          {metrics.win_rate.toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {metrics.winning_positions_count}W / {metrics.losing_positions_count}L
        </div>
      </div>

      {/* Positions Count */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Open Positions</div>
        <div className="text-2xl font-bold text-gray-900">
          {metrics.open_positions_count}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Active holdings
        </div>
      </div>

      {/* Concentration */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Top 3 Concentration</div>
        <div className="text-2xl font-bold text-gray-900">
          {metrics.top_3_concentration.toFixed(1)}%
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Largest: {metrics.largest_position_pct.toFixed(1)}%
        </div>
      </div>

      {/* Cost Basis */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600 mb-1">Cost Basis</div>
        <div className="text-2xl font-bold text-gray-900">
          {formatCurrency(metrics.total_cost_basis)}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Total invested
        </div>
      </div>
    </div>
  );
}
