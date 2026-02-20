from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Alpha Vantage
    alpha_vantage_api_key: str = ""

    # Polygon.io
    polygon_api_key: str = ""

    # Twitter/X
    twitter_bearer_token: str = ""

    # App config
    environment: str = "development"
    log_level: str = "INFO"

    # Frontend
    next_public_api_base_url: str = "http://localhost:8000"

    @property
    def tickers_list(self) -> List[str]:
        """Get current watchlist tickers from persistent storage."""
        from backend.core import watchlist_manager
        return watchlist_manager.get_tickers()

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
