import { WatchlistTable } from "@/components/watchlist/WatchlistTable";
import { EarningsCalendar } from "@/components/watchlist/EarningsCalendar";
import { AddTickerForm } from "@/components/watchlist/AddTickerForm";
import { TrendingStocks } from "@/components/watchlist/TrendingStocks";

export default function WatchlistPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">◉ Watchlist</h1>
        <div className="text-xs text-gray-500">Click any row to view deep research</div>
      </div>
      <AddTickerForm />
      <EarningsCalendar />
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <WatchlistTable />
      </div>
      <TrendingStocks />
    </div>
  );
}
