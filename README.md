# Market Intelligence Platform

Professional stock market intelligence with real-time data, analytics, and automated report generation.

## Features

### Market Data
- **Macro Overview**: VIX, major indices (SPY/QQQ/IWM), treasury yields, market regime detection
- **Sector Rotation**: Real-time sector performance vs SPY with heatmap visualization
- **Market Breadth**: Advance/decline ratios, MA breadth, new highs/lows, breadth scoring
- **Technical Analysis**: Multi-timeframe charts with indicators (MA, RSI, MACD, Bollinger Bands)

### Watchlist Intelligence
- **Price Monitoring**: Real-time price tracking with volume analysis
- **Fundamentals**: P/E, market cap, analyst ratings, price targets, earnings dates
- **Options Flow**: Unusual options activity detection with volume/OI analysis
- **Implied Volatility**: ATM IV, IV rank, expected moves, put/call skew, term structure
- **Deep Research**: Comprehensive stock analysis with earnings history, insider transactions

### Analytics
- **Short Squeeze Scoring**: Ranks tickers by squeeze potential (short interest, days to cover, volume)
- **Correlation Matrix**: 3-month pairwise return correlations across watchlist
- **ML Signals**: RSI divergence, MACD crossovers, BB squeeze, golden/death cross detection
- **Earnings Calendar**: Upcoming earnings dates grouped by proximity

### Sentiment Analysis
- **Reddit Trending**: Top posts from WSB/stocks/investing with ticker mentions
- **News Sentiment**: Real-time news aggregation with sentiment scoring
- **StockTwits**: Social sentiment tracking with bull/bear ratios
- **Flow Toxicity**: Options flow pinning analysis

### Report Generation
- **Daily Market Report**: Pre-market (6:30 AM) and post-market (5:00 PM) automated reports
- **Advanced Analytics**: EOD analytics report (4:30 PM) with ML signals, correlation, squeeze scores
- **Deep Research**: On-demand detailed stock research reports with charts and fundamentals

## Tech Stack

### Backend
- **FastAPI**: High-performance async API framework
- **yfinance**: Real-time market data
- **PRAW**: Reddit data integration
- **Plotly**: Interactive chart generation
- **Jinja2**: HTML report templating
- **APScheduler**: Automated report scheduling
- **Pydantic**: Data validation and serialization

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **SWR**: Data fetching with caching
- **date-fns**: Date formatting

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Reddit API credentials (for sentiment analysis)

### 1. Clone & Setup

```bash
git clone <your-repo>
cd market-research
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env with your API keys

# Start backend
uvicorn backend.main:app --reload
```

Backend runs on: http://localhost:8000

### 3. Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start frontend
npm run dev
```

Frontend runs on: http://localhost:3000

## Configuration

### Environment Variables

```bash
# Required
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MarketIntelligence/1.0

# Optional
TWITTER_BEARER_TOKEN=your_token  # For Twitter integration (future)
ALPHA_VANTAGE_API_KEY=your_key   # For alternative data sources
```

### Watchlist Configuration

Edit `backend/config.py` to customize your watchlist tickers:

```python
tickers_list = ["AAPL", "NVDA", "TSLA", "IBM", "CVNA", "SPY", "QQQ", "IWM"]
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

**Market Data**
- `GET /api/market/snapshot` — Macro overview
- `GET /api/market/sectors` — Sector rotation
- `GET /api/market/breadth` — Market breadth metrics
- `GET /api/market/technicals/{ticker}` — Technical analysis
- `GET /api/market/iv/{ticker}` — Implied volatility analytics
- `GET /api/market/options/{ticker}` — Options data (max pain, gamma)

**Watchlist**
- `GET /api/watchlist/` — All watchlist tickers
- `GET /api/watchlist/{ticker}` — Stock detail with fundamentals
- `GET /api/watchlist/earnings-calendar` — Upcoming earnings

**Analytics**
- `GET /api/analytics/squeeze` — Short squeeze leaderboard
- `GET /api/analytics/correlation` — Correlation matrix
- `GET /api/analytics/signals/{ticker}` — ML signals

**Sentiment**
- `GET /api/sentiment/reddit` — Reddit trending
- `GET /api/sentiment/news/{ticker}` — News sentiment
- `GET /api/sentiment/stocktwits/{ticker}` — StockTwits sentiment
- `GET /api/sentiment/flow-toxicity/{ticker}` — Flow toxicity

**Reports**
- `POST /api/reports/generate/{type}` — Generate report (daily/analytics/research)
- `GET /api/reports/` — List all reports
- `GET /api/reports/view/{id}` — View report HTML
- `GET /api/reports/download/{id}` — Download report
- `DELETE /api/reports/{id}` — Delete report

## Scheduled Jobs

The scheduler runs these jobs automatically:

| Job | Schedule | Description |
|-----|----------|-------------|
| Market Snapshot | Every 5 min | Updates macro data |
| Watchlist Refresh | Every 5 min | Updates stock prices |
| Sector Rotation | Every 10 min | Updates sector performance |
| Market Breadth | Every 10 min | Updates breadth metrics |
| Reddit Sentiment | Every 30 min | Scrapes Reddit posts |
| Analytics Scores | 4:30 PM ET Mon-Fri | Computes squeeze/correlation |
| Daily Report (Pre) | 6:30 AM ET Mon-Fri | Generates pre-market report |
| Daily Report (Post) | 5:00 PM ET Mon-Fri | Generates post-market report |
| Analytics Report | 4:30 PM ET Mon-Fri | Generates EOD analytics report |

## Project Structure

```
market-research/
├── backend/
│   ├── api/routes/          # FastAPI route handlers
│   ├── core/                # Cache, rate limiter, scheduler
│   ├── engines/             # Data fetching engines
│   │   ├── analytics/       # ML signals, correlation, squeeze
│   │   ├── market_data/     # Macro, sectors, technicals, breadth
│   │   ├── sentiment/       # Reddit, news, flow toxicity
│   │   └── watchlist/       # Price data, fundamentals, options flow
│   ├── models/              # Pydantic data models
│   ├── report_engine/       # Report generation
│   │   ├── templates/       # Jinja2 HTML templates
│   │   └── renderers/       # Chart and table renderers
│   ├── data/                # Cache and report storage
│   ├── config.py            # Configuration
│   └── main.py              # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   └── lib/             # Utilities, types, API clients
│   └── package.json
├── .env                     # Environment variables (not committed)
├── .env.example             # Example env file
└── README.md
```

## Cache System

- **TTLs**: 5min (real-time data), 15min (technicals), 1hr (fundamentals), 24hr (earnings)
- **After-hours**: TTLs are 6x longer when markets are closed
- **Storage**: File-based JSON cache in `backend/data/cache/`
- **Invalidation**: Automatic via scheduler, manual via refresh endpoints

## Rate Limiting

- **yfinance**: 0.5s delay between requests
- **Reddit**: 1 request per second (PRAW handles this)
- Prevents API bans and ensures reliable data fetching

## Development

### Backend Testing
```bash
cd backend
pytest  # Run tests (if implemented)
```

### Frontend Development
```bash
cd frontend
npm run dev     # Development server
npm run build   # Production build
npm run lint    # ESLint
```

### Code Quality
- Backend: Type hints with Pydantic
- Frontend: TypeScript with strict mode
- Linting: ESLint for frontend
- Formatting: Consistent style throughout

## Deployment

### Backend (Production)

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Production)

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Environment
- Set `NEXT_PUBLIC_API_BASE_URL` to your backend URL
- Configure CORS in `backend/main.py` for your domain
- Use environment variables for all API keys

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (requires 3.11+)
- Verify `.env` file exists with required credentials
- Check if port 8000 is available

### Frontend shows API errors
- Verify backend is running on http://localhost:8000
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_API_BASE_URL` in `.env.local`

### Reddit data not loading
- Verify Reddit API credentials in `.env`
- Check rate limits haven't been exceeded
- Ensure `REDDIT_USER_AGENT` is set

### Reports not generating
- Check `backend/data/reports/` directory exists and is writable
- Verify scheduler is running (check logs)
- Ensure sufficient disk space

## License

This is a personal project for educational and informational purposes.

**Disclaimer**: This software is for informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

## Support

For issues or questions, please open an issue on the GitHub repository.

---

Built with FastAPI, Next.js, and market data APIs. Powered by real-time financial data.
