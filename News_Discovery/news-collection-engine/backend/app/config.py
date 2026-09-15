import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Multi-Source News Collection Engine"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./news_engine.db"

    # Redis Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL_SECONDS: int = 300

    # API Keys
    NEWSAPI_KEY: Optional[str] = None
    GNEWS_API_KEY: Optional[str] = None
    NEWSDATA_API_KEY: Optional[str] = None

    # Resiliency
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    HTTP_TIMEOUT_SECONDS: float = 10.0

    # Scheduled Fetcher & Caching Layer Settings
    FETCH_INTERVAL_MINUTES: int = 15
    RETENTION_PERIOD_DAYS: int = 7
    ENABLE_SCHEDULED_FETCHER: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
