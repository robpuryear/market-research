# Testing Checklist

## Backend API Tests

### Health & Status
- [ ] `GET /health` returns 200
- [ ] `GET /api/scheduler/status` shows all jobs

### Market Data
- [ ] `GET /api/market/snapshot` returns VIX, indices, yields
- [ ] `GET /api/market/sectors` returns 11 sector ETFs
- [ ] `GET /api/market/breadth` returns breadth metrics
- [ ] `GET /api/market/technicals/AAPL` returns OHLCV + indicators
- [ ] `GET /api/market/iv/AAPL` returns IV analytics
- [ ] `GET /api/market/options/AAPL` returns max pain, gamma, P/C ratio

### Watchlist
- [ ] `GET /api/watchlist/` returns all tickers with prices
- [ ] `GET /api/watchlist/AAPL` returns fundamentals + insider data
- [ ] `GET /api/watchlist/earnings-calendar` returns upcoming earnings

### Analytics
- [ ] `GET /api/analytics/squeeze` returns ranked squeeze scores
- [ ] `GET /api/analytics/correlation` returns correlation matrix
- [ ] `GET /api/analytics/signals/AAPL` returns ML signals (may be empty)

### Sentiment
- [ ] `GET /api/sentiment/reddit` returns top posts + ticker mentions
- [ ] `GET /api/sentiment/stocktwits/AAPL` returns social sentiment
- [ ] `GET /api/sentiment/news/AAPL` returns news articles with sentiment
- [ ] `GET /api/sentiment/flow-toxicity/AAPL` returns pin score + toxicity

### Reports
- [ ] `POST /api/reports/generate/daily` creates job
- [ ] `POST /api/reports/generate/analytics` creates job
- [ ] `POST /api/reports/generate/research?ticker=AAPL` creates job
- [ ] `GET /api/reports/status/{job_id}` returns job status
- [ ] `GET /api/reports/` lists all reports
- [ ] `GET /api/reports/view/{id}` serves HTML
- [ ] `GET /api/reports/download/{id}` downloads file
- [ ] `DELETE /api/reports/{id}` deletes report

## Frontend Tests

### Pages Load
- [ ] `/` — Dashboard
- [ ] `/market` — Market page
- [ ] `/watchlist` — Watchlist page
- [ ] `/watchlist/AAPL` — Stock detail page
- [ ] `/analytics` — Analytics page
- [ ] `/sentiment` — Sentiment page
- [ ] `/reports` — Reports page

### Dashboard Components
- [ ] Macro panel shows VIX, market regime
- [ ] Index levels show SPY/QQQ/IWM with % changes
- [ ] Sector heatmap displays color-coded sectors
- [ ] Market breadth shows A/D ratio and scores
- [ ] Watchlist table displays tickers with prices
- [ ] Earnings calendar shows upcoming earnings

### Market Page
- [ ] All dashboard components render
- [ ] Charts are interactive (if using Plotly)
- [ ] Data refreshes every 5 minutes

### Watchlist Page
- [ ] Earnings calendar shows "This Week / Next Week / Later"
- [ ] Table is sortable by columns
- [ ] Clicking ticker navigates to detail page

### Stock Detail Page
- [ ] IV Analytics panel shows IV rank, expected moves
- [ ] Options panel shows max pain, gamma, P/C ratio
- [ ] Stock detail panel shows fundamentals
- [ ] Earnings history displays
- [ ] Insider transactions display
- [ ] "Generate Report" button works

### Analytics Page
- [ ] Short squeeze table displays with color coding
- [ ] Correlation heatmap shows all tickers
- [ ] ML signals feed has ticker selector
- [ ] Signal cards show direction badges

### Sentiment Page
- [ ] Reddit feed shows top posts
- [ ] Ticker mentions show counts
- [ ] StockTwits panel (if implemented)
- [ ] News sentiment panel (if implemented)

### Reports Page
- [ ] Generate buttons create new reports
- [ ] Report cards display with metadata
- [ ] "View" button opens report viewer
- [ ] "Download" button downloads HTML
- [ ] Delete button (🗑️) removes report with confirmation
- [ ] Reports auto-refresh after generation

## Integration Tests

### Data Flow
- [ ] Backend cache persists between requests
- [ ] Frontend SWR cache prevents duplicate requests
- [ ] Auto-refresh intervals work correctly
- [ ] Loading states display during fetches
- [ ] Error states display on API failures

### Scheduler
- [ ] Jobs run at scheduled times
- [ ] Reports auto-generate at 6:30 AM, 4:30 PM, 5:00 PM
- [ ] Analytics scores refresh at 4:30 PM
- [ ] Market data refreshes every 5-10 minutes

### Report Generation
- [ ] Daily reports include VIX, sectors, watchlist
- [ ] Analytics reports include signals, correlation, squeeze
- [ ] Research reports include charts, fundamentals, insider data
- [ ] Reports are viewable in iframe
- [ ] Reports are downloadable as standalone HTML

## Performance Tests

### Response Times
- [ ] Health check: < 50ms
- [ ] Market snapshot: < 2s
- [ ] Watchlist bulk: < 3s
- [ ] Stock detail: < 5s
- [ ] Report generation: < 10s

### Cache Hit Rates
- [ ] Repeated requests return from cache
- [ ] Cache invalidation works correctly
- [ ] TTLs are respected

## Security Tests

### Environment
- [ ] `.env` file is not committed to git
- [ ] API keys are loaded from environment
- [ ] No secrets in code

### CORS
- [ ] Frontend can call backend (localhost:3000 → localhost:8000)
- [ ] Unauthorized origins are blocked

### Input Validation
- [ ] Invalid tickers return 404/400
- [ ] Malformed requests return error messages
- [ ] SQL injection not possible (using yfinance, not DB)

## Browser Compatibility

- [ ] Chrome/Edge — All features work
- [ ] Firefox — All features work
- [ ] Safari — All features work
- [ ] Mobile responsive (optional)

## Error Handling

### API Errors
- [ ] 404 returns meaningful message
- [ ] 500 shows error details
- [ ] Network errors display user-friendly message

### Data Errors
- [ ] Missing data shows "—" or placeholder
- [ ] Invalid ticker returns error
- [ ] Rate limit exceeded handled gracefully

## Documentation

- [ ] README.md is complete
- [ ] API docs at /docs are accurate
- [ ] .env.example has all required keys
- [ ] Code comments are clear

## Deployment Readiness

- [ ] `./start.sh` starts both servers
- [ ] All dependencies are in requirements.txt / package.json
- [ ] No hard-coded paths (use relative paths)
- [ ] Environment variables are configurable
- [ ] Production build works (`npm run build`)

---

## Test Results

Date: _______
Tester: _______

**Pass Rate**: _____ / _____ tests passed

**Critical Issues**:
- 

**Minor Issues**:
- 

**Notes**:
- 
