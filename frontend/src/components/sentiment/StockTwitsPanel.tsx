"use client";
import { useStockTwits } from "@/hooks/useSentiment";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

const TICKERS = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL", "IBM"];

function TwitsMeter({ ticker }: { ticker: string }) {
  const { data, isLoading } = useStockTwits(ticker);

  if (isLoading) return (
    <div className="bg-white border border-gray-300 rounded-lg p-4 flex items-center justify-center h-28">
      <LoadingSpinner />
    </div>
  );

  if (!data) return null;

  const { bullish_count, bearish_count, total_messages, sentiment_label } = data;
  const labeled = bullish_count + bearish_count;
  const bullPct = labeled > 0 ? Math.round((bullish_count / labeled) * 100) : 50;
  const bearPct = 100 - bullPct;

  const labelColor =
    sentiment_label === "Bullish" ? "text-green-600" :
    sentiment_label === "Bearish" ? "text-red-600" :
    "text-gray-700";

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-sm text-blue-600">{ticker}</span>
        <span className={`text-xs font-semibold ${labelColor}`}>{sentiment_label}</span>
      </div>

      {/* Bull/Bear bar */}
      {labeled > 0 ? (
        <>
          <div className="flex rounded-full overflow-hidden h-2 mb-1">
            <div className="bg-green-500 transition-all" style={{ width: `${bullPct}%` }} />
            <div className="bg-red-500 transition-all" style={{ width: `${bearPct}%` }} />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span className="text-green-700">&#9650; {bullish_count} bullish</span>
            <span className="text-red-700">{bearish_count} bearish &#9660;</span>
          </div>
        </>
      ) : (
        <div className="text-xs text-gray-500 mt-1">No labeled messages</div>
      )}
      <div className="text-xs text-gray-500 mt-2">{total_messages} messages analyzed</div>
    </div>
  );
}

export function StockTwitsPanel() {
  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">
        StockTwits Sentiment
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {TICKERS.map((t) => (
          <TwitsMeter key={t} ticker={t} />
        ))}
      </div>
    </div>
  );
}
