import type { Position } from "@/lib/types";

interface PositionsTableProps {
  positions: Position[];
  onAddToPosition: (position: Position) => void;
  onSellPosition: (position: Position) => void;
}

export function PositionsTable({ positions, onAddToPosition, onSellPosition }: PositionsTableProps) {
  const formatCurrency = (value: number | null) => {
    if (value === null) return "—";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number | null) => {
    if (value === null) return "—";
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const getColorClass = (value: number | null) => {
    if (value === null) return "text-gray-600";
    if (value > 0) return "text-green-600";
    if (value < 0) return "text-red-600";
    return "text-gray-600";
  };

  if (positions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <div className="text-gray-400 text-lg mb-2">No positions yet</div>
        <p className="text-gray-500 text-sm">
          Add your first position to start tracking your portfolio.
        </p>
      </div>
    );
  }

  // Sort by unrealized P&L (best performers first)
  const sortedPositions = [...positions].sort((a, b) => {
    const aVal = a.unrealized_pnl || 0;
    const bVal = b.unrealized_pnl || 0;
    return bVal - aVal;
  });

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Ticker</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Shares</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Avg Cost</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Current Price</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Value</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">P&L</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">P&L %</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Days</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sortedPositions.map((position) => (
              <tr
                key={position.id}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3">
                  <div className="font-bold text-gray-900">{position.ticker}</div>
                  {position.notes && (
                    <div className="text-xs text-gray-500 mt-0.5">{position.notes}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-900">
                  {position.quantity.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-600">
                  {formatCurrency(position.avg_cost_basis)}
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-900">
                  {formatCurrency(position.current_price)}
                </td>
                <td className="px-4 py-3 text-right font-mono font-semibold text-gray-900">
                  {formatCurrency(position.current_value)}
                </td>
                <td className={`px-4 py-3 text-right font-mono font-bold ${getColorClass(position.unrealized_pnl)}`}>
                  {formatCurrency(position.unrealized_pnl)}
                </td>
                <td className={`px-4 py-3 text-right font-mono font-bold ${getColorClass(position.unrealized_pnl_pct)}`}>
                  {formatPercent(position.unrealized_pnl_pct)}
                </td>
                <td className="px-4 py-3 text-center text-gray-600">
                  {position.days_held !== null ? position.days_held : "—"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => onAddToPosition(position)}
                      className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                      title="Add more shares"
                    >
                      Add
                    </button>
                    <button
                      onClick={() => onSellPosition(position)}
                      className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                      title="Sell shares"
                    >
                      Sell
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
