"use client";
import { useRedditSentiment } from "@/hooks/useSentiment";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { clsx } from "clsx";

export function RedditFeed() {
  const { data, isLoading } = useRedditSentiment();

  if (isLoading) return <LoadingSpinner />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* Trending tickers */}
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Trending Tickers</div>
        <div className="flex flex-wrap gap-2">
          {data.trending_tickers.map((t, i) => (
            <span key={t} className="bg-gray-100 text-gray-800 px-3 py-1 rounded font-mono text-sm">
              #{i + 1} {t}
            </span>
          ))}
        </div>
      </div>

      {/* Ticker sentiment */}
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">
          Ticker Mentions (Analyzed {data.total_posts_analyzed || "mock"} posts)
        </div>
        <div className="space-y-2">
          {data.ticker_mentions.slice(0, 8).map((m) => (
            <div key={m.ticker} className="flex items-center gap-3">
              <span className="text-blue-600 font-mono text-sm w-14">{m.ticker}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                <div
                  className={clsx(
                    "h-full rounded-full transition-all",
                    m.sentiment_score > 0.1 ? "bg-green-500" : m.sentiment_score < -0.1 ? "bg-red-500" : "bg-slate-400"
                  )}
                  style={{ width: `${Math.min(100, m.mention_count * 2)}%` }}
                />
              </div>
              <span className="text-gray-500 text-xs w-12 text-right">{m.mention_count} 🔔</span>
              <span className={clsx("text-xs w-12 text-right", m.sentiment_score > 0.1 ? "text-green-600" : m.sentiment_score < -0.1 ? "text-red-600" : "text-gray-500")}>
                {m.sentiment_score > 0 ? "+" : ""}{m.sentiment_score.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Posts */}
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Top Posts</div>
        <div className="space-y-3">
          {data.top_posts.slice(0, 10).map((post, i) => (
            <a
              key={i}
              href={post.url}
              target="_blank"
              rel="noopener noreferrer"
              className={clsx(
                "block border-l-2 pl-3 py-1 hover:bg-gray-100/30 transition-colors",
                post.sentiment === "positive" ? "border-green-500" : post.sentiment === "negative" ? "border-red-500" : "border-gray-300"
              )}
            >
              <div className="text-sm text-gray-800 leading-tight">{post.title}</div>
              <div className="text-xs text-gray-500 mt-1 flex gap-3">
                <span>r/{post.subreddit}</span>
                <span>▲ {post.score.toLocaleString()}</span>
                {post.tickers_mentioned.length > 0 && <span className="text-blue-600">{post.tickers_mentioned.join(", ")}</span>}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
