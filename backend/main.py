import logging
import math
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import market, watchlist, sentiment, reports, scheduler as scheduler_routes, analytics
from core import scheduler as sched

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class NaNSafeJSONResponse(JSONResponse):
    """Custom JSON response that converts NaN/Inf to null."""
    def render(self, content) -> bytes:
        # Recursively clean NaN/Inf values
        cleaned_content = self._clean_nans(content)
        return json.dumps(
            cleaned_content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

    @staticmethod
    def _clean_nans(obj):
        """Recursively replace NaN and Inf with None."""
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, dict):
            return {k: NaNSafeJSONResponse._clean_nans(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [NaNSafeJSONResponse._clean_nans(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(NaNSafeJSONResponse._clean_nans(item) for item in obj)
        return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scheduler on startup, stop on shutdown."""
    logger.info("Starting Market Intelligence API")
    sched.start()
    yield
    logger.info("Shutting down Market Intelligence API")
    sched.stop()


app = FastAPI(
    title="Market Intelligence API",
    description="Professional stock market intelligence with real-time data, analytics, and report generation",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=NaNSafeJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://market-research-one-delta.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(market.router)
app.include_router(watchlist.router)
app.include_router(sentiment.router)
app.include_router(reports.router)
app.include_router(scheduler_routes.router)
app.include_router(analytics.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
