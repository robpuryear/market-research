import { ShortSqueezeTable } from "@/components/analytics/ShortSqueezeTable";
import { CorrelationHeatmap } from "@/components/analytics/CorrelationHeatmap";
import { MLSignalsFeed } from "@/components/analytics/MLSignalsFeed";

export default function AnalyticsPage() {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">
          ◎ Analytics
        </h1>
        <div className="text-xs text-gray-500">Refreshes every 10 minutes</div>
      </div>

      <ShortSqueezeTable />
      <CorrelationHeatmap />
      <MLSignalsFeed />
    </div>
  );
}
