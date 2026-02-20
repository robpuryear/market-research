"""Dark pool data placeholder — requires Polygon.io premium access."""
from datetime import datetime, timezone
from models.sentiment import DarkPoolData
from config import settings
import logging

logger = logging.getLogger(__name__)


async def get_dark_pool(ticker: str) -> DarkPoolData:
    """Return dark pool data. Placeholder until Polygon key with dark pool access."""
    if not settings.polygon_api_key or settings.polygon_api_key == "your_polygon_key":
        return _placeholder(ticker)

    # TODO: implement with Polygon dark pool endpoint when available
    return _placeholder(ticker)


def _placeholder(ticker: str) -> DarkPoolData:
    return DarkPoolData(
        ticker=ticker,
        dark_pool_volume=None,
        dark_pool_pct=None,
        block_trades=[],
        sentiment=None,
        is_placeholder=True,
        timestamp=datetime.now(timezone.utc),
    )
