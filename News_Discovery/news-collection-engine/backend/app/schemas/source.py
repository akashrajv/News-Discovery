from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class SourceBase(BaseModel):
    name: str
    source_type: str  # API, RSS, AUTHORIZED_FEED
    connection_method: str  # api, rss, authorized_feed
    api_endpoint: Optional[str] = None
    api_key_env_name: Optional[str] = None
    rss_url: Optional[str] = None
    enabled: bool = True
    priority: int = Field(default=5, ge=1, le=10)
    request_limit: int = 100
    rate_limit_window_seconds: int = 86400
    estimated_cost_per_request: float = 0.0

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    request_limit: Optional[int] = None
    rss_url: Optional[str] = None
    api_endpoint: Optional[str] = None

class SourceRead(SourceBase):
    id: str
    api_key_configured: bool
    last_successful_collection: Optional[datetime] = None
    last_error: Optional[str] = None
    requests_used: int = 0
    requests_used_today: int = 0
    requests_remaining: int = 100
    last_reset_at: Optional[datetime] = None
    next_reset_utc: Optional[datetime] = None
    current_status: str = "AVAILABLE"
    retry_after: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
