"use client";
import { useSectors } from "@/hooks/useMarketData";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { clsx } from "clsx";

function heatColor(value: number): string {
  if (value >= 2) return "bg-green-100 text-green-700";
  if (value >= 0.5) return "bg-green-50 text-green-600";
  if (value >= 0) return "bg-gray-50 text-gray-700";
  if (value >= -0.5) return "bg-red-50 text-red-600";
  if (value >= -2) return "bg-red-100 text-red-700";
  return "bg-red-200 text-red-800";
}

export function SectorHeatmap() {
  const { data: sectors, isLoading } = useSectors();

  if (isLoading) return <LoadingSpinner />;
  if (!sectors) return null;

  const sorted = [...sectors].sort((a, b) => b.change_1d - a.change_1d);

  return (
    <div>
      <div className="grid grid-cols-4 md:grid-cols-6 gap-2">
        {sorted.map((s) => (
          <div
            key={s.ticker}
            className={clsx(
              "rounded-lg p-3 text-center transition-transform hover:scale-105 cursor-default",
              heatColor(s.change_1d)
            )}
          >
            <div className="font-bold text-sm font-mono">{s.ticker}</div>
            <div className="text-xs opacity-75 mt-0.5">{s.name.split(" ")[0]}</div>
            <div className="text-sm font-bold mt-1">
              {s.change_1d >= 0 ? "+" : ""}{s.change_1d.toFixed(2)}%
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="text-gray-500 border-b border-gray-300">
              <th className="text-left py-1 px-2">ETF</th>
              <th className="text-right py-1 px-2">1D</th>
              <th className="text-right py-1 px-2">5D</th>
              <th className="text-right py-1 px-2">1M</th>
              <th className="text-right py-1 px-2">vs SPY</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => (
              <tr key={s.ticker} className="border-b border-gray-300 hover:bg-gray-50">
                <td className="py-1 px-2 text-gray-700 font-bold">{s.ticker} <span className="text-gray-500">{s.name}</span></td>
                <td className={`text-right py-1 px-2 ${s.change_1d >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {s.change_1d >= 0 ? "+" : ""}{s.change_1d.toFixed(2)}%
                </td>
                <td className={`text-right py-1 px-2 ${s.change_5d >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {s.change_5d >= 0 ? "+" : ""}{s.change_5d.toFixed(2)}%
                </td>
                <td className={`text-right py-1 px-2 ${s.change_1m >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {s.change_1m >= 0 ? "+" : ""}{s.change_1m.toFixed(2)}%
                </td>
                <td className={`text-right py-1 px-2 ${s.vs_spy_1d >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {s.vs_spy_1d >= 0 ? "+" : ""}{s.vs_spy_1d.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
