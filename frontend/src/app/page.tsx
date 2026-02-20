import { MacroPanel } from "@/components/market/MacroPanel";
import { IndexLevels } from "@/components/market/IndexLevels";
import { SectorHeatmap } from "@/components/market/SectorHeatmap";
import { BreadthPanel } from "@/components/market/BreadthPanel";
import { WatchlistTable } from "@/components/watchlist/WatchlistTable";
import { EarningsCalendar } from "@/components/watchlist/EarningsCalendar";

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">
          ◈ Dashboard
        </h1>
        <div className="text-xs text-gray-500">
          Auto-refreshes every 5 minutes
        </div>
      </div>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
          Macro Overview
        </div>
        <MacroPanel />
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
          Major Indices
        </div>
        <IndexLevels />
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
          Sector Rotation
        </div>
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <SectorHeatmap />
        </div>
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
          Market Breadth
        </div>
        <BreadthPanel />
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
          Watchlist
        </div>
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <WatchlistTable compact />
        </div>
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
          Earnings Calendar
        </div>
        <EarningsCalendar />
      </section>
    </div>
  );
}
