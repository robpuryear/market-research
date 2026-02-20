"use client";
import { useOptions } from "@/hooks/useMarketData";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

interface Props {
  ticker: string;
}

function GammaBar({ value }: { value: number | null }) {
  if (value == null) return <span className="text-gray-400">—</span>;
  const isPositive = value >= 0;
  const width = Math.min(100, Math.abs(value) / 10);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full ${isPositive ? "bg-green-500" : "bg-red-500"}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className={`text-xs font-mono font-semibold ${isPositive ? "text-green-700" : "text-red-700"}`}>
        {isPositive ? "+" : ""}{value.toFixed(2)}M
      </span>
    </div>
  );
}

export function OptionsPanel({ ticker }: Props) {
  const { data, error, isLoading } = useOptions(ticker);

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-400 font-mono">Loading options data…</div>
      </div>
    );
  }

  if (error || !data || data.expiry === "N/A") {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-400 font-mono">
          {error ? "Failed to load options data" : "No options data available"}
        </div>
      </div>
    );
  }

  const pcrColor =
    data.put_call_ratio == null
      ? "text-gray-500"
      : data.put_call_ratio > 1.2
      ? "text-red-600"
      : data.put_call_ratio < 0.8
      ? "text-green-600"
      : "text-gray-700";

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-gray-700 font-mono">Options Analytics</div>
          <div className="text-xs text-gray-500 mt-0.5">Expiry: {data.expiry}</div>
        </div>
        <div className="text-xs text-gray-400 font-mono">{ticker}</div>
      </div>

      <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Max Pain */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1 flex items-center gap-1">
            Max Pain <InfoIcon tooltip={TOOLTIPS.maxPain} />
          </div>
          <div className="text-xl font-bold font-mono text-gray-800">
            {data.max_pain != null ? `$${data.max_pain.toFixed(2)}` : "—"}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Options settlement target price
          </div>
        </div>

        {/* Put/Call Ratio */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1 flex items-center gap-1">
            Put/Call Ratio <InfoIcon tooltip={TOOLTIPS.putCallRatio} />
          </div>
          <div className={`text-xl font-bold font-mono ${pcrColor}`}>
            {data.put_call_ratio != null ? data.put_call_ratio.toFixed(3) : "—"}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            <span className="flex items-center gap-1">
              {data.total_put_oi?.toLocaleString() ?? "—"} put OI / {data.total_call_oi?.toLocaleString() ?? "—"} call OI
            </span>
          </div>
        </div>

        {/* Gamma Exposure */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
            Gamma Exposure <InfoIcon tooltip={TOOLTIPS.gammaExposure} />
          </div>
          <GammaBar value={data.gamma_exposure} />
          <div className="text-xs text-gray-500 mt-2">
            Net dealer gamma (approx)
          </div>
        </div>
      </div>
    </div>
  );
}
