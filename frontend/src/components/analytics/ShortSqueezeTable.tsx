"use client";
import { useState } from "react";
import { useSqueeze } from "@/hooks/useAnalytics";
import type { SqueezeScore } from "@/lib/types";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

type SortKey = "squeeze_score" | "short_interest_pct" | "short_ratio" | "volume_ratio";

function rowColor(score: number): string {
  if (score >= 70) return "bg-red-50 border-red-200";
  if (score >= 40) return "bg-yellow-50 border-yellow-200";
  return "bg-green-50 border-green-200";
}

function scoreColor(score: number): string {
  if (score >= 70) return "text-red-700 font-bold";
  if (score >= 40) return "text-yellow-700 font-semibold";
  return "text-green-700";
}

export function ShortSqueezeTable() {
  const { data, error, isLoading } = useSqueeze();
  const [sortKey, setSortKey] = useState<SortKey>("squeeze_score");
  const [sortAsc, setSortAsc] = useState(false);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((a) => !a);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-sm text-gray-500 font-mono">Loading squeeze scores…</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-sm text-red-500 font-mono">Failed to load squeeze data</div>
      </div>
    );
  }

  const sorted = [...data].sort((a, b) => {
    const av = a[sortKey] ?? -Infinity;
    const bv = b[sortKey] ?? -Infinity;
    return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  function ColHeader({ label, k, tooltip }: { label: string; k: SortKey; tooltip?: string }) {
    const active = sortKey === k;
    return (
      <th
        className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide cursor-pointer hover:text-blue-700 select-none"
        onClick={() => handleSort(k)}
      >
        <span className="flex items-center gap-1">
          {label}{active ? (sortAsc ? " ↑" : " ↓") : ""}
          {tooltip && <InfoIcon tooltip={tooltip} />}
        </span>
      </th>
    );
  }

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="text-sm font-semibold text-gray-700 font-mono">Short Squeeze Leaderboard</div>
        <div className="text-xs text-gray-500 mt-0.5">Ranked by squeeze score (0–100)</div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm font-mono">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide w-8">#</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">Ticker</th>
              <ColHeader label="Score" k="squeeze_score" tooltip={TOOLTIPS.squeezeScore} />
              <ColHeader label="Short %" k="short_interest_pct" tooltip={TOOLTIPS.shortInterest} />
              <ColHeader label="Days to Cover" k="short_ratio" tooltip={TOOLTIPS.daysTocover} />
              <ColHeader label="Vol Ratio" k="volume_ratio" tooltip={TOOLTIPS.volumeRatio} />
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
                <span className="flex items-center gap-1">
                  Options <InfoIcon tooltip={TOOLTIPS.unusualOptions} />
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={row.ticker} className={`border-b border-gray-100 ${rowColor(row.squeeze_score)}`}>
                <td className="px-3 py-2 text-gray-400 text-xs">{i + 1}</td>
                <td className="px-3 py-2 text-blue-700 font-bold">{row.ticker}</td>
                <td className={`px-3 py-2 ${scoreColor(row.squeeze_score)}`}>
                  {row.squeeze_score.toFixed(1)}
                </td>
                <td className="px-3 py-2 text-gray-700">
                  {row.short_interest_pct != null ? `${row.short_interest_pct.toFixed(1)}%` : "—"}
                </td>
                <td className="px-3 py-2 text-gray-700">
                  {row.short_ratio != null ? `${row.short_ratio.toFixed(1)}d` : "—"}
                </td>
                <td className="px-3 py-2 text-gray-700">
                  {row.volume_ratio.toFixed(2)}x
                </td>
                <td className="px-3 py-2">
                  {row.options_unusual ? (
                    <span className="text-xs bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded">Unusual</span>
                  ) : (
                    <span className="text-xs text-gray-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
