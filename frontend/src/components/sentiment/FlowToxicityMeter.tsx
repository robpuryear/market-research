"use client";
import { useFlowToxicity } from "@/hooks/useSentiment";
import { Badge } from "@/components/ui/Badge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

export function FlowToxicityMeter({ ticker }: { ticker: string }) {
  const { data, isLoading } = useFlowToxicity(ticker);

  if (isLoading) return <LoadingSpinner size="sm" />;
  if (!data) return null;

  const pct = data.pin_score * 100;
  const color = pct < 20 ? "bg-green-500" : pct < 40 ? "bg-yellow-500" : pct < 60 ? "bg-orange-500" : "bg-red-500";

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-mono text-gray-800 flex items-center gap-1">
          {ticker} Flow Toxicity (PIN Model) <InfoIcon tooltip={TOOLTIPS.flowToxicity} />
        </div>
        <Badge variant={data.toxicity_regime.toLowerCase() as "low" | "elevated" | "high" | "extreme"}>
          {data.toxicity_regime}
        </Badge>
      </div>
      <div className="text-2xl font-bold text-gray-900 font-mono mb-2">{data.pin_score.toFixed(3)}</div>
      <div className="bg-gray-100 rounded-full h-2 overflow-hidden">
        <div className={`${color} h-full rounded-full transition-all`} style={{ width: `${Math.min(100, pct)}%` }} />
      </div>
      <div className="text-xs text-gray-500 mt-2">{data.interpretation}</div>
    </div>
  );
}
