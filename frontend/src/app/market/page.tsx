import { MacroPanel } from "@/components/market/MacroPanel";
import { IndexLevels } from "@/components/market/IndexLevels";
import { SectorHeatmap } from "@/components/market/SectorHeatmap";
import { BreadthPanel } from "@/components/market/BreadthPanel";

export default function MarketPage() {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">▦ Market Overview</h1>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">Macro Conditions</div>
        <MacroPanel />
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">Major Indices</div>
        <IndexLevels />
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">Sector Performance</div>
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <SectorHeatmap />
        </div>
      </section>

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">Market Breadth</div>
        <BreadthPanel />
      </section>
    </div>
  );
}
