"use client";
import { RedditFeed } from "@/components/sentiment/RedditFeed";
import { SentimentGauge } from "@/components/sentiment/SentimentGauge";
import { FlowToxicityMeter } from "@/components/sentiment/FlowToxicityMeter";
import { StockTwitsPanel } from "@/components/sentiment/StockTwitsPanel";
import { NewsSentimentPanel } from "@/components/sentiment/NewsSentimentPanel";
import { useRedditSentiment } from "@/hooks/useSentiment";

const FLOW_TICKERS = ["SPY", "QQQ", "NVDA", "TSLA", "AAPL"];

export default function SentimentPage() {
  const { data: redditData } = useRedditSentiment();
  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">&#9670; Sentiment</h1>

      <SentimentGauge />

      <StockTwitsPanel />

      <NewsSentimentPanel />

      <section>
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">Flow Toxicity (PIN Model)</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {FLOW_TICKERS.map((t) => (
            <FlowToxicityMeter key={t} ticker={t} />
          ))}
        </div>
      </section>

      {redditData && (
        <section>
          <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest mb-3">Reddit Sentiment</div>
          <RedditFeed />
        </section>
      )}
    </div>
  );
}
