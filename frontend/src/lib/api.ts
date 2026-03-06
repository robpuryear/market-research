import { API_BASE_URL } from "./constants";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";
import type {
  MarketSnapshot,
  MarketBreadth,
  IVAnalytics,
  TechnicalData,
  SectorData,
  StockData,
  StockDetailData,
  RedditSentimentData,
  FlowToxicityData,
  StockTwitsSentiment,
  NewsSentimentData,
  ReportMeta,
  ReportJobStatus,
  SchedulerJob,
  MLSignalsData,
  SqueezeScore,
  CorrelationMatrix,
  EarningsCalendarEntry,
  ScanCandidate,
  CompositeSentiment,
  BacktestConfig,
  BacktestResult,
  StrategyInfo,
  OptionsChain,
  OptionsAnalytics,
  ExpirationDate,
  SpreadLeg,
  SpreadAnalysis,
  Alert,
  AlertNotification,
  PriceCondition,
  SignalCondition,
  EarningsCondition,
  Position,
  Transaction,
  PortfolioMetrics,
  Strategy,
  StrategyResult,
  ConditionGroup,
  TrendingStock,
} from "./types";

// OptionsGreeks type (from backend model)
export interface OptionsGreeks {
  ticker: string;
  expiry: string;
  max_pain: number | null;
  gamma_exposure: number | null;
  put_call_ratio: number | null;
  total_call_oi: number | null;
  total_put_oi: number | null;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

// --- Market ------------------------------------------------------------------
export const fetchSnapshot = () =>
  apiFetch<MarketSnapshot>("/api/market/snapshot");

export const fetchTechnicals = (ticker: string) =>
  apiFetch<TechnicalData>(`/api/market/technicals/${ticker}`);

export const fetchSectors = () =>
  apiFetch<SectorData[]>("/api/market/sectors");

export const fetchBreadth = () =>
  apiFetch<MarketBreadth>("/api/market/breadth");

export const fetchIV = (ticker: string) =>
  apiFetch<IVAnalytics>(`/api/market/iv/${ticker}`);

export const refreshCache = () =>
  apiFetch<{ message: string }>("/api/market/refresh", { method: "POST" });

// --- Watchlist ----------------------------------------------------------------
export const fetchWatchlist = () =>
  apiFetch<StockData[]>("/api/watchlist/");

export const fetchStockDetail = (ticker: string) =>
  apiFetch<StockDetailData>(`/api/watchlist/${ticker}`);

export const addToWatchlist = (ticker: string) =>
  apiFetch<{ status: string; ticker: string }>("/api/watchlist/add", {
    method: "POST",
    body: JSON.stringify({ ticker }),
  });

export const removeFromWatchlist = (ticker: string) =>
  apiFetch<{ status: string; ticker: string }>(`/api/watchlist/remove/${ticker}`, {
    method: "DELETE",
  });

// --- Sentiment ----------------------------------------------------------------
export const fetchRedditSentiment = () =>
  apiFetch<RedditSentimentData>("/api/sentiment/reddit");

export const fetchFlowToxicity = (ticker: string) =>
  apiFetch<FlowToxicityData>(`/api/sentiment/flow-toxicity/${ticker}`);

export const fetchStockTwits = (ticker: string) =>
  apiFetch<StockTwitsSentiment>(`/api/sentiment/stocktwits/${ticker}`);

export const fetchNewsSentiment = async (ticker: string): Promise<NewsSentimentData | null> => {
  const res = await fetch(`${API_BASE_URL}/api/sentiment/news/${ticker}`, {
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    },
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API /api/sentiment/news/${ticker} failed (${res.status}): ${text}`);
  }
  return res.json();
};

// --- Reports -----------------------------------------------------------------
export const fetchReports = () =>
  apiFetch<ReportMeta[]>("/api/reports/");

export const generateReport = (type: "daily" | "analytics" | "research", ticker?: string) =>
  apiFetch<{ job_id: string; status: string }>(
    `/api/reports/generate/${type}${ticker ? `?ticker=${encodeURIComponent(ticker)}` : ""}`,
    { method: "POST" },
  );

export const fetchJobStatus = (jobId: string) =>
  apiFetch<ReportJobStatus>(`/api/reports/status/${jobId}`);

export const deleteReport = (reportId: string) =>
  apiFetch<{ status: string; report_id: string }>(`/api/reports/${reportId}`, {
    method: "DELETE",
  });

export const getReportViewUrl = (reportId: string) =>
  `${API_BASE_URL}/api/reports/view/${reportId}`;

export const getReportDownloadUrl = (reportId: string) =>
  `${API_BASE_URL}/api/reports/download/${reportId}`;

// --- Scheduler ---------------------------------------------------------------
export const fetchSchedulerStatus = () =>
  apiFetch<SchedulerJob[]>("/api/scheduler/status");

// --- Analytics ---------------------------------------------------------------
export const fetchSqueeze = () =>
  apiFetch<SqueezeScore[]>("/api/analytics/squeeze");

export const fetchCorrelation = () =>
  apiFetch<CorrelationMatrix>("/api/analytics/correlation");

export const fetchSignals = (ticker: string) =>
  apiFetch<MLSignalsData>(`/api/analytics/signals/${ticker}`);

export const fetchEarningsCalendar = () =>
  apiFetch<EarningsCalendarEntry[]>("/api/watchlist/earnings-calendar");

export const fetchOptions = (ticker: string) =>
  apiFetch<OptionsGreeks>(`/api/market/options/${ticker}`);

export const fetchMarketScan = (params?: {
  universe?: string;
  limit?: number;
  min_price?: number;
  max_price?: number;
  min_composite?: number;
  top_n?: number;
}) => {
  const queryParams = new URLSearchParams();
  if (params?.universe) queryParams.set("universe", params.universe);
  if (params?.limit !== undefined) queryParams.set("limit", params.limit.toString());
  if (params?.min_price !== undefined) queryParams.set("min_price", params.min_price.toString());
  if (params?.max_price !== undefined) queryParams.set("max_price", params.max_price.toString());
  if (params?.min_composite !== undefined) queryParams.set("min_composite", params.min_composite.toString());  // Fixed: now includes 0!
  if (params?.top_n !== undefined) queryParams.set("top_n", params.top_n.toString());

  const url = `/api/analytics/market-scan${queryParams.toString() ? `?${queryParams}` : ""}`;
  return apiFetch<ScanCandidate[]>(url);
};

export const fetchCompositeSentiment = (ticker: string) =>
  apiFetch<CompositeSentiment>(`/api/analytics/composite-sentiment/${ticker}`);

export const fetchTrending = (topN = 15) =>
  apiFetch<TrendingStock[]>(`/api/analytics/trending?top_n=${topN}`);

// Backtest API
export const fetchBacktestStrategies = () =>
  apiFetch<{ strategies: StrategyInfo[] }>('/api/backtest/strategies');

export const runBacktest = (config: BacktestConfig) =>
  apiFetch<BacktestResult>('/api/backtest/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

// Options API
export const fetchOptionsChain = (ticker: string, expiration?: string) => {
  const url = expiration
    ? `/api/options/chain/${ticker}?expiration=${expiration}`
    : `/api/options/chain/${ticker}`;
  return apiFetch<OptionsChain>(url);
};

export const fetchOptionsExpirations = (ticker: string) =>
  apiFetch<ExpirationDate[]>(`/api/options/expirations/${ticker}`);

export const fetchOptionsAnalytics = (ticker: string) =>
  apiFetch<OptionsAnalytics>(`/api/options/analytics/${ticker}`);

export const analyzeSpread = (request: { ticker: string; spot_price: number; legs: SpreadLeg[]; spread_type?: string }) =>
  apiFetch<SpreadAnalysis>('/api/options/spread/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

// Alerts API
export const fetchAlerts = () =>
  apiFetch<Alert[]>("/api/alerts/");

export const createAlert = (alert: { ticker: string; alert_type: string; condition: PriceCondition | SignalCondition | EarningsCondition; notification_methods?: string[]; message?: string }) =>
  apiFetch<Alert>("/api/alerts/", {
    method: "POST",
    body: JSON.stringify(alert),
  });

export const updateAlert = (alertId: string, updates: Partial<Alert>) =>
  apiFetch<Alert>(`/api/alerts/${alertId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });

export const deleteAlert = (alertId: string) =>
  apiFetch(`/api/alerts/${alertId}`, { method: "DELETE" });

export const fetchNotifications = (limit = 50, unreadOnly = false) =>
  apiFetch<AlertNotification[]>(`/api/alerts/notifications/?limit=${limit}&unread_only=${unreadOnly}`);

export const markNotificationRead = (notifId: string) =>
  apiFetch(`/api/alerts/notifications/${notifId}/read`, { method: "PATCH" });

// Portfolio API
export const fetchPositions = (includeClosed = false) =>
  apiFetch<Position[]>(`/api/portfolio/positions?include_closed=${includeClosed}`);

export const fetchPosition = (positionId: string) =>
  apiFetch<Position>(`/api/portfolio/positions/${positionId}`);

export const addPosition = (position: { ticker: string; quantity: number; price: number; date: string; notes?: string }) =>
  apiFetch<Position>("/api/portfolio/positions", {
    method: "POST",
    body: JSON.stringify(position),
  });

export const sellPosition = (positionId: string, sale: { quantity: number; price: number; date: string; notes?: string }) =>
  apiFetch<Position>(`/api/portfolio/positions/${positionId}/sell`, {
    method: "POST",
    body: JSON.stringify(sale),
  });

export const updatePosition = (positionId: string, updates: { notes?: string }) =>
  apiFetch<Position>(`/api/portfolio/positions/${positionId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });

export const deletePosition = (positionId: string) =>
  apiFetch(`/api/portfolio/positions/${positionId}`, { method: "DELETE" });

export const fetchPortfolioMetrics = (cash = 0) =>
  apiFetch<PortfolioMetrics>(`/api/portfolio/metrics?cash=${cash}`);

export const fetchTransactions = (positionId?: string) =>
  apiFetch<Transaction[]>(`/api/portfolio/transactions${positionId ? `?position_id=${positionId}` : ""}`);

// --- Strategies --------------------------------------------------------------

export const fetchStrategies = () =>
  apiFetch<Strategy[]>("/api/strategies/");

export const fetchStrategy = (strategyId: string) =>
  apiFetch<Strategy>(`/api/strategies/${strategyId}`);

export const createStrategy = (strategy: {
  name: string;
  description?: string;
  entry_conditions: ConditionGroup;
  exit_conditions?: ConditionGroup;
  enabled?: boolean;
  scope?: "watchlist" | "market";
  generate_alerts?: boolean;
}) =>
  apiFetch<Strategy>("/api/strategies/", {
    method: "POST",
    body: JSON.stringify(strategy),
  });

export const updateStrategy = (strategyId: string, updates: Partial<Strategy>) =>
  apiFetch<Strategy>(`/api/strategies/${strategyId}`, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });

export const deleteStrategy = (strategyId: string) =>
  apiFetch(`/api/strategies/${strategyId}`, { method: "DELETE" });

export const runStrategy = (strategyId: string) =>
  apiFetch<StrategyResult[]>(`/api/strategies/${strategyId}/run`, { method: "POST" });

export const fetchStrategyResults = (strategyId: string, limit = 100) =>
  apiFetch<StrategyResult[]>(`/api/strategies/${strategyId}/results?limit=${limit}`);

export const fetchRecentStrategyResults = (limit = 50) =>
  apiFetch<StrategyResult[]>(`/api/strategies/results/recent?limit=${limit}`);
