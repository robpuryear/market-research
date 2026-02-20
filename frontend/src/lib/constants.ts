export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const WATCHLIST_TICKERS = [
  "IBM",
  "CVNA",
  "NVDA",
  "TSLA",
  "AAPL",
  "SPY",
  "QQQ",
  "IWM",
];

export const REFRESH_INTERVALS = {
  market: 5 * 60 * 1000,      // 5 min
  watchlist: 5 * 60 * 1000,   // 5 min
  sentiment: 30 * 60 * 1000,  // 30 min
  reports: 60 * 1000,          // 60 sec
  scheduler: 30 * 1000,        // 30 sec
};
