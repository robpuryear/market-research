// Centralized tooltip content for all metrics

export const TOOLTIPS = {
  // Market Macro Metrics
  vix: "VIX (Volatility Index) - Measures expected market volatility. <15 = Low fear, 15-20 = Normal, 20-30 = Elevated, >30 = High fear/panic",
  fearGreed: "Fear & Greed Index - Market sentiment gauge combining multiple indicators. 0-25 = Extreme Fear (buy signal), 25-45 = Fear, 45-55 = Neutral, 55-75 = Greed, 75-100 = Extreme Greed (caution)",
  spy: "S&P 500 ETF - Tracks the 500 largest US companies. Primary market benchmark.",
  qqq: "Nasdaq 100 ETF - Tracks the 100 largest non-financial companies on Nasdaq. Tech-heavy.",
  iwm: "Russell 2000 ETF - Tracks 2000 small-cap US stocks. Risk-on indicator.",
  tenYear: "10-Year Treasury Yield - Risk-free rate. Rising = tightening conditions, Falling = easing conditions",
  twoYear: "2-Year Treasury Yield - Short-term rate tied to Fed policy. Rising = hawkish Fed, Falling = dovish Fed",
  yieldSpread: "10Y-2Y Yield Spread - Difference between long and short rates. Negative = recession warning (inverted curve)",
  marketRegime: "Current market environment based on VIX, breadth, and momentum. Helps determine strategy.",

  // Market Breadth
  advanceDecline: "Advance/Decline Ratio - Stocks rising vs falling. >1.5 = Strong breadth, <0.67 = Weak breadth",
  ma20Breadth: "% Above 20-day MA - Stocks trending up short-term. >70% = Overbought, <30% = Oversold",
  ma50Breadth: "% Above 50-day MA - Stocks trending up medium-term. >60% = Strong, <40% = Weak",
  ma200Breadth: "% Above 200-day MA - Stocks in long-term uptrend. >50% = Bull market, <50% = Bear market",
  newHighsLows: "New Highs vs New Lows - Market health indicator. Positive = healthy, Negative = deteriorating",

  // Stock Fundamentals
  pe: "P/E Ratio (Price/Earnings) - Price relative to earnings. <15 = Cheap, 15-25 = Fair, >25 = Expensive (varies by sector)",
  marketCap: "Market Capitalization - Total company value. Large-cap (>$10B) = stable, Small-cap (<$2B) = volatile",
  avgVolume: "Average Daily Volume - Typical shares traded. Higher = more liquid/easier to trade",
  analystRating: "Analyst Consensus - Average rating from Wall Street analysts. 1.0-1.5 = Strong Buy, 4.5-5.0 = Sell",
  earningsDate: "Next Earnings Report - When company reports quarterly results. Volatility often spikes around earnings",

  // IV Analytics
  atmIV: "At-The-Money Implied Volatility - Expected stock movement. Higher = bigger expected moves (good for options sellers)",
  ivRank: "IV Rank - Current IV vs 52-week range. >80 = Very high, <20 = Very low. High IV = good for selling options",
  expectedMoveWeekly: "Expected Weekly Move - Predicted price range for next week based on options pricing",
  expectedMoveMonthly: "Expected Monthly Move - Predicted price range for next month based on options pricing",
  ivTermStructure: "IV Term Structure - How IV changes across expirations. Upward = normal, Flat/inverted = event risk",

  // Options Metrics
  maxPain: "Max Pain - Price where most options expire worthless. Theory: stocks gravitate toward this price at expiration",
  gammaExposure: "Gamma Exposure (GEX) - Market maker positioning. Positive = resistance to moves, Negative = amplifies moves",
  putCallRatio: "Put/Call Ratio - Put volume vs call volume. >1.0 = Bearish bias, <0.7 = Bullish bias, 0.7-1.0 = Neutral",
  totalCallOI: "Total Call Open Interest - Outstanding call contracts. Shows bullish positioning",
  totalPutOI: "Total Put Open Interest - Outstanding put contracts. Shows bearish positioning or hedging",

  // Short Squeeze Metrics
  squeezeScore: "Squeeze Score - Likelihood of short squeeze. >70 = High potential, 40-70 = Moderate, <40 = Low",
  shortInterest: "Short Interest % - Shares sold short as % of float. >20% = Heavily shorted, <5% = Lightly shorted",
  daysTocover: "Days To Cover - Days to close all short positions at avg volume. >10 = High squeeze risk",
  volumeRatio: "Volume Ratio - Current vs average volume. >2.0 = High interest, <0.5 = Low interest",
  unusualOptions: "Unusual Options Activity - Detected abnormal options flow. Often precedes big moves",

  // ML Signals
  rsi: "RSI (Relative Strength Index) - Momentum oscillator. >70 = Overbought, <30 = Oversold, 40-60 = Neutral",
  macd: "MACD - Trend-following momentum. Crossovers signal trend changes. Above signal line = bullish",
  bollingerBands: "Bollinger Bands - Volatility bands. Price at upper band = overbought, lower band = oversold",
  goldenCross: "Golden Cross - 50-day MA crosses above 200-day MA. Strong bullish signal",
  deathCross: "Death Cross - 50-day MA crosses below 200-day MA. Strong bearish signal",

  // Sentiment Metrics
  redditMentions: "Reddit Mentions - Times ticker mentioned on WSB/investing subs. High mentions = retail interest/hype",
  sentimentScore: "Sentiment Score - Aggregate positive/negative tone. >0.6 = Bullish, <0.4 = Bearish, 0.4-0.6 = Neutral",
  stockTwitsBullish: "StockTwits Bullish % - Users expressing bullish sentiment. >70% = Very bullish, <30% = Very bearish",
  newsSentiment: "News Sentiment - AI-analyzed news tone. Positive = good news flow, Negative = bad news flow",
  flowToxicity: "Flow Toxicity - Options order flow aggression. >0.5 = Toxic (whale activity), <0.3 = Benign (retail)",

  // Correlation
  correlation: "Correlation - How two stocks move together. +1.0 = Perfect correlation, -1.0 = Perfect inverse, 0 = Unrelated",
  correlationMatrix: "Correlation Matrix - Shows how each stock pair moves together over 3 months. Use to identify diversification opportunities (low correlation) or sector trends (high correlation). Green = positive correlation, Red = negative correlation.",

  // ML Signals
  mlSignalsFeed: "ML Signals Feed - Real-time technical analysis signals detected by machine learning algorithms. Signals include RSI divergence, MACD crossovers, Bollinger Band squeezes, and moving average crosses. Bullish signals suggest upward momentum, bearish signals suggest downward pressure.",

  // Scanner Composite Score
  compositeScore: "Composite Score - Weighted combination of squeeze potential (30%), ML signals (25%), options activity (25%), IV rank (10%), and volume (10%). Higher = better opportunity",

  // Composite Sentiment
  compositeSentiment: "Composite Sentiment Score - Multi-factor sentiment analysis combining News Sentiment (30%), Analyst Ratings & Price Targets (20%), Insider Trading Activity (15%), Options Flow & Unusual Activity (20%), and Technical Momentum (15%). Score ranges from -100 (very bearish) to +100 (very bullish). Higher confidence = more data available for analysis.",

  // Report Types
  dailyReport: "Pre-market (6:30 AM) and post-market (5:00 PM) market summary with macro data and watchlist overview",
  analyticsReport: "End-of-day (4:30 PM) deep analytics: ML signals, correlation matrix, and short squeeze scores",
  researchReport: "On-demand comprehensive stock analysis with fundamentals, technicals, sentiment, and options data",
  scannerReport: "End-of-day (4:45 PM) market scanner results showing top opportunities across all universes",
};

export function getTooltip(key: string): string {
  return TOOLTIPS[key as keyof typeof TOOLTIPS] || "No description available";
}
