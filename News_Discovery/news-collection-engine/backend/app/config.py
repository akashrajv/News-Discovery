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

    # Relational Database (SQLAlchemy / SQLite fallback)
    DATABASE_URL: str = "sqlite:///./news_engine.db"

    # MongoDB Configuration (Primary Article Document Store)
    MONGODB_URL: Optional[str] = None
    MONGODB_DB_NAME: str = "news_discovery"
    ARTICLE_STORAGE_BACKEND: str = "both"  # "both", "mongodb", "relational"

    # Redis Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL_SECONDS: int = 300

    # API Keys
    NEWSAPI_KEY: Optional[str] = None
    GNEWS_API_KEY: Optional[str] = None
    NEWSDATA_API_KEY: Optional[str] = None

    # Qdrant Vector Database (Semantic Discovery)
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "news_articles"
    QDRANT_STORAGE_PATH: str = "./qdrant_storage"

    # DeepSeek-R1 AI Reasoning Engine
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-reasoner"

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
