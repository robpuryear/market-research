"use client";
import { useMarketSnapshot } from "@/hooks/useMarketData";
import { DataCard } from "@/components/ui/DataCard";
import { Badge } from "@/components/ui/Badge";
import { LoadingCard } from "@/components/ui/LoadingSpinner";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

export function MacroPanel() {
  const { data, isLoading, error } = useMarketSnapshot();

  if (isLoading) return <div className="grid grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <LoadingCard key={i} />)}</div>;
  if (error) return <div className="text-red-600 text-sm p-4">Failed to load market data: {error.message}</div>;
  if (!data) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <DataCard
        label={
          <span className="flex items-center gap-1">
            VIX <InfoIcon tooltip={TOOLTIPS.vix} />
          </span>
        }
        value={data.vix.toFixed(2)}
        sub={<Badge variant={data.vix_regime.toLowerCase() as "low" | "elevated" | "high" | "extreme"}>{data.vix_regime}</Badge>}
      />
      <DataCard
        label={
          <span className="flex items-center gap-1">
            Fear & Greed <InfoIcon tooltip={TOOLTIPS.fearGreed} />
          </span>
        }
        value={data.fear_greed_approx}
        sub={
          <span className={data.fear_greed_approx >= 60 ? "text-green-600" : data.fear_greed_approx <= 40 ? "text-red-600" : "text-gray-500"}>
            {data.fear_greed_approx >= 60 ? "Greed" : data.fear_greed_approx <= 40 ? "Fear" : "Neutral"}
          </span>
        }
      />
      <DataCard
        label={
          <span className="flex items-center gap-1">
            Market Regime <InfoIcon tooltip={TOOLTIPS.marketRegime} />
          </span>
        }
        value={<Badge variant={data.market_regime.toLowerCase() as "bull" | "bear" | "neutral" | "volatile"}>{data.market_regime}</Badge>}
        sub=""
      />
      <DataCard
        label={
          <span className="flex items-center gap-1">
            10Y Yield <InfoIcon tooltip={TOOLTIPS.tenYear} />
          </span>
        }
        value={data.yield_10y != null ? `${data.yield_10y}%` : "—"}
        sub={data.yield_spread != null ? (
          <span className={data.yield_spread >= 0 ? "text-green-600" : "text-red-600"}>
            Spread: {data.yield_spread > 0 ? "+" : ""}{data.yield_spread?.toFixed(3)}%
            {data.yield_spread < 0 ? " (Inverted)" : ""}
            <InfoIcon tooltip={TOOLTIPS.yieldSpread} className="ml-1" />
          </span>
        ) : undefined}
      />
    </div>
  );
}
