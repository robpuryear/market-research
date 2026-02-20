// Mirror of backend Pydantic models

export interface MLSignal {
  signal_type: string;
  direction: "bullish" | "bearish" | "neutral";
  description: string;
}

export interface MLSignalsData {
  ticker: string;
  signals: MLSignal[];
  rsi: number;
  signal_count: number;
  timestamp: string;
}

export interface SqueezeScore {
  ticker: string;
  squeeze_score: number;
  short_interest_pct: number | null;
  short_ratio: number | null;
  volume_ratio: number;
  options_unusual: boolean;
}

export interface CorrelationMatrix {
  tickers: string[];
  matrix: number[][];
  timestamp: string;
}

export interface EarningsCalendarEntry {
  ticker: string;
  earnings_date: string;
  days_until: number;
}

export interface EarningsEntry {
  date: string;
  eps_estimate: number | null;
  eps_actual: number | null;
  surprise_pct: number | null;
}

export interface IVAnalytics {
  ticker: string;
  atm_iv: number;
  iv_rank: number;
  expected_move_1w: number;
  expected_move_1m: number;
  put_call_skew: number;
  term_structure: number[];
  timestamp: string;
}

export interface MarketBreadth {
  advancers: number;
  decliners: number;
  unchanged: number;
  advance_decline_ratio: number;
  pct_above_20ma: number;
  pct_above_50ma: number;
  pct_above_200ma: number;
  new_highs_52w: number;
  new_lows_52w: number;
  avg_rsi: number;
  breadth_score: number;
  timestamp: string;
}

export interface IndexData {
  ticker: string;
  price: number;
  change_pct: number;
  ma_20: number | null;
  ma_50: number | null;
  ma_200: number | null;
  above_200ma: boolean | null;
  support: number[];
  resistance: number[];
  rsi: number | null;
  volume: number | null;
  volume_ratio: number | null;
}

export interface MarketSnapshot {
  vix: number;
  vix_regime: "Low" | "Elevated" | "High" | "Extreme";
  fear_greed_approx: number;
  yield_10y: number | null;
  yield_2y: number | null;
  yield_spread: number | null;
  market_regime: "Bull" | "Bear" | "Neutral" | "Volatile";
  spy: IndexData;
  qqq: IndexData;
  iwm: IndexData;
  timestamp: string;
}

export interface TechnicalData {
  ticker: string;
  dates: string[];
  opens: (number | null)[];
  highs: (number | null)[];
  lows: (number | null)[];
  closes: (number | null)[];
  volumes: (number | null)[];
  ma_20: (number | null)[];
  ma_50: (number | null)[];
  ma_200: (number | null)[];
  rsi: (number | null)[];
  macd_line: (number | null)[];
  macd_signal: (number | null)[];
  macd_histogram: (number | null)[];
  bb_upper: (number | null)[];
  bb_middle: (number | null)[];
  bb_lower: (number | null)[];
  support_levels: number[];
  resistance_levels: number[];
  current_signal: "bullish" | "bearish" | "neutral";
}

export interface SectorData {
  ticker: string;
  name: string;
  price: number;
  change_1d: number;
  change_5d: number;
  change_1m: number;
  vs_spy_1d: number;
  vs_spy_5d: number;
  vs_spy_1m: number;
}

export interface StockData {
  ticker: string;
  price: number;
  change_pct: number;
  volume: number;
  avg_volume: number;
  volume_ratio: number;
  market_cap: number | null;
  pe_ratio: number | null;
  short_interest_pct: number | null;
  analyst_rating: string | null;
  price_target: number | null;
  earnings_date: string | null;
  options_unusual: boolean;
  insider_activity: string | null;
  squeeze_score: number | null;
  timestamp: string;
}

export interface InsiderTransaction {
  name: string;
  transaction: string;
  shares: number;
  value: number;
  date: string;
}

export interface OptionsFlowData {
  ticker: string;
  expiry: string;
  strike: number;
  option_type: "call" | "put";
  volume: number;
  open_interest: number;
  volume_oi_ratio: number;
  premium_total: number;
  is_unusual: boolean;
  timestamp: string;
}

export interface StockDetailData extends StockData {
  company_name: string;
  sector: string | null;
  industry: string | null;
  forward_pe: number | null;
  pb_ratio: number | null;
  debt_to_equity: number | null;
  revenue_growth: number | null;
  short_ratio: number | null;
  price_target_low: number | null;
  price_target_high: number | null;
  earnings_surprise_pct: number | null;
  profit_margin: number | null;
  return_on_equity: number | null;
  return_on_assets: number | null;
  dividend_yield: number | null;
  free_cash_flow: number | null;
  week_52_high: number | null;
  week_52_low: number | null;
  earnings_history: EarningsEntry[];
  insider_transactions: InsiderTransaction[];
  institutional_ownership_pct: number | null;
  unusual_options: OptionsFlowData[];
}

export interface RedditPost {
  title: string;
  subreddit: string;
  score: number;
  url: string;
  tickers_mentioned: string[];
  sentiment: "positive" | "negative" | "neutral";
  created_utc: number;
}

export interface TickerMention {
  ticker: string;
  mention_count: number;
  sentiment_score: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
}

export interface RedditSentimentData {
  top_posts: RedditPost[];
  ticker_mentions: TickerMention[];
  trending_tickers: string[];
  total_posts_analyzed: number;
  subreddits: string[];
  timestamp: string;
}

export interface FlowToxicityData {
  ticker: string;
  pin_score: number;
  buy_volume: number;
  sell_volume: number;
  total_volume: number;
  toxicity_regime: "Low" | "Moderate" | "High" | "Extreme";
  interpretation: string;
  timestamp: string;
}

export interface ReportMeta {
  id: string;
  type: "daily" | "analytics" | "research";
  ticker: string | null;
  generated_at: string;
  path: string;
  file_size_kb: number | null;
  title: string;
}

export interface ReportJobStatus {
  job_id: string;
  report_type: "daily" | "analytics" | "research";
  ticker: string | null;
  status: "pending" | "running" | "complete" | "error";
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  report_id: string | null;
}

export interface SchedulerJob {
  id: string;
  name: string;
  next_run: string | null;
  status: string;
}

export interface StockTwitsSentiment {
  ticker: string;
  bullish_count: number;
  bearish_count: number;
  total_messages: number;
  sentiment_ratio: number;
  sentiment_label: "Bullish" | "Bearish" | "Neutral";
  recent_messages: string[];
  timestamp: string;
}

export interface NewsArticle {
  title: string;
  url: string;
  source: string;
  sentiment_score: number;
  sentiment_label: string;
  relevance_score: number;
  published_at: string;
}

export interface NewsSentimentData {
  ticker: string;
  avg_sentiment_score: number;
  sentiment_label: string;
  article_count: number;
  articles: NewsArticle[];
  timestamp: string;
}

export interface ScanCandidate {
  ticker: string;
  company_name: string;
  price: number;
  volume_ratio: number;
  squeeze_score: number;
  ml_signals: MLSignal[];
  bullish_signal_count: number;
  bearish_signal_count: number;
  unusual_options_count: number;
  iv_rank: number;
  composite_score: number;
  short_interest_pct: number | null;
  market_cap: number | null;
  sector: string | null;
  timestamp: string;
}
