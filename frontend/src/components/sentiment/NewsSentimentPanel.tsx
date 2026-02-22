"use client";
import { useState } from "react";
import { useNewsSentiment } from "@/hooks/useSentiment";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { WATCHLIST_TICKERS } from "@/lib/constants";

const SCORE_COLOR = (score: number) =>
  score >= 0.35 ? "text-green-600" :
  score >= 0.05 ? "text-emerald-600" :
  score <= -0.35 ? "text-red-600" :
  score <= -0.05 ? "text-orange-600" :
  "text-gray-700";

const LABEL_BG = (label: string) => {
  if (label.includes("Bullish")) return "bg-green-100/40 text-green-600";
  if (label.includes("Bearish")) return "bg-red-100/40 text-red-600";
  return "bg-gray-100 text-gray-700";
};

function ArticleRow({ article }: { article: { title: string; url: string; source: string; sentiment_score: number; sentiment_label: string; published_at: string } }) {
  const date = article.published_at
    ? article.published_at.slice(0, 8).replace(/(\d{4})(\d{2})(\d{2})/, "$1-$2-$3")
    : "";

  return (
    <div className="flex items-start gap-3 py-2 border-b border-gray-300 last:border-0">
      <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${LABEL_BG(article.sentiment_label)}`}>
        {article.sentiment_label}
      </span>
      <div className="flex-1 min-w-0">
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-gray-800 hover:text-blue-600 transition-colors line-clamp-1"
        >
          {article.title}
        </a>
        <div className="text-xs text-gray-500 mt-0.5">{article.source} &middot; {date}</div>
      </div>
      <span className={`shrink-0 text-xs font-mono ${SCORE_COLOR(article.sentiment_score)}`}>
        {article.sentiment_score >= 0 ? "+" : ""}{article.sentiment_score.toFixed(2)}
      </span>
    </div>
  );
}

function NewsFeed({ ticker }: { ticker: string }) {
  const { data, isLoading } = useNewsSentiment(ticker);

  if (isLoading) return <div className="flex justify-center py-6"><LoadingSpinner /></div>;

  if (!data) {
    return (
      <div className="text-xs text-gray-500 py-4 text-center">
        News sentiment unavailable (API timeout or no data)
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-4">
        <div className={`text-sm font-semibold px-3 py-1 rounded ${LABEL_BG(data.sentiment_label)}`}>
          {data.sentiment_label}
        </div>
        <div className="text-xs text-gray-500">
          Avg score: <span className={`font-mono ${SCORE_COLOR(data.avg_sentiment_score)}`}>
            {data.avg_sentiment_score >= 0 ? "+" : ""}{data.avg_sentiment_score.toFixed(3)}
          </span>
        </div>
        <div className="text-xs text-gray-500">{data.article_count} articles</div>
      </div>
      <div>
        {data.articles.slice(0, 10).map((a, i) => (
          <ArticleRow key={i} article={a} />
        ))}
      </div>
    </div>
  );
}

export function NewsSentimentPanel() {
  const tickers = WATCHLIST_TICKERS.filter((t) => !["SPY", "QQQ", "IWM"].includes(t));
  const [selected, setSelected] = useState(tickers[0] || "NVDA");

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest">News Sentiment (Finnhub)</div>
        <div className="flex gap-1 flex-wrap justify-end">
          {tickers.map((t) => (
            <button
              key={t}
              onClick={() => setSelected(t)}
              className={`px-2 py-0.5 text-xs rounded font-mono transition-colors ${
                selected === t
                  ? "bg-purple-700 text-white"
                  : "bg-gray-50 text-gray-500 hover:bg-gray-100"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <NewsFeed ticker={selected} />
    </div>
  );
}
