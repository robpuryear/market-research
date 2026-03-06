from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Alpha Vantage
    alpha_vantage_api_key: str = ""

    # Finnhub
    finnhub_api_key: str = ""

    # Polygon.io
    polygon_api_key: str = ""

    # Twitter/X
    twitter_bearer_token: str = ""

    # App config
    environment: str = "development"
    log_level: str = "INFO"

    # Frontend
    next_public_api_base_url: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql+asyncpg://localhost/market_research"

    # API auth (empty = disabled for local dev)
    api_key: str = ""

    @property
    def async_database_url(self) -> str:
        """Normalize Render's postgres:// URL to postgresql+asyncpg://"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
