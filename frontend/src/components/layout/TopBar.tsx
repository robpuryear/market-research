"use client";
import { useMarketSnapshot } from "@/hooks/useMarketData";
import { RefreshButton } from "@/components/ui/RefreshButton";
import { Badge } from "@/components/ui/Badge";

export function TopBar() {
  const { data: snapshot } = useMarketSnapshot();

  return (
    <header className="h-14 bg-gray-50 border-b border-gray-300 flex items-center justify-between px-6">
      <div className="flex items-center gap-6">
        {snapshot && (
          <>
            <div className="flex items-center gap-2 font-mono text-sm">
              <span className="text-gray-500">VIX</span>
              <span className="text-gray-900 font-bold">{snapshot.vix}</span>
              <Badge variant={snapshot.vix_regime.toLowerCase() as "low" | "elevated" | "high" | "extreme"}>
                {snapshot.vix_regime}
              </Badge>
            </div>
            <div className="flex items-center gap-2 font-mono text-sm">
              <span className="text-gray-500">SPY</span>
              <span className="text-gray-900 font-bold">${snapshot.spy.price.toFixed(2)}</span>
              <span className={snapshot.spy.change_pct >= 0 ? "text-green-600" : "text-red-600"}>
                {snapshot.spy.change_pct >= 0 ? "+" : ""}{snapshot.spy.change_pct.toFixed(2)}%
              </span>
            </div>
            <div className="flex items-center gap-2 font-mono text-sm">
              <span className="text-gray-500">Regime</span>
              <Badge variant={snapshot.market_regime.toLowerCase() as "bull" | "bear" | "neutral" | "volatile"}>
                {snapshot.market_regime}
              </Badge>
            </div>
          </>
        )}
      </div>
      <RefreshButton />
    </header>
  );
}
