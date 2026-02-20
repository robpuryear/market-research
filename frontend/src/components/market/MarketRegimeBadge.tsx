"use client";
import { useMarketSnapshot } from "@/hooks/useMarketData";
import { Badge } from "@/components/ui/Badge";

export function MarketRegimeBadge() {
  const { data } = useMarketSnapshot();
  if (!data) return null;
  return (
    <Badge variant={data.market_regime.toLowerCase() as "bull" | "bear" | "neutral" | "volatile"}>
      {data.market_regime} Market
    </Badge>
  );
}
