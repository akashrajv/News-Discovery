from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.article import ArticleRead

class CollectionRequestInput(BaseModel):
    entity: Optional[str] = Field(default="Tata Motors", description="Target entity/company or comma-separated list of companies")
    entities: Optional[List[str]] = Field(default_factory=list, description="List of target companies for multi-company batch collection")
    keywords: List[str] = Field(default_factory=list, description="Keywords for news query filtering")
    location: Optional[str] = Field(default="Global", description="Target geographical region")
    category: Optional[str] = Field(default="Automotive", description="Topic category filter")
    time_window_minutes: int = Field(default=60, description="Recency time window in minutes (10, 30, 60, 360, 1440)")
    min_relevance: Optional[float] = Field(default=60.0, ge=0.0, le=100.0, description="Minimum relevance score threshold (0-100) to retain articles")

class CollectionResponse(BaseModel):
    status: str  # success, partial_success, failed
    request_id: str
    articles_collected: int
    duplicates_removed: int
    low_relevance_filtered: int = 0
    cache_hits: int
    cache_misses: int
    sources_used: int
    sources_failed: int
    api_requests: int
    rss_collections: int
    estimated_api_cost: float
    articles: List[ArticleRead]
    routing_summary: Optional[Dict[str, Any]] = None
    demo_mode: bool = False
    message: Optional[str] = None

class CollectionHistoryRead(BaseModel):
    id: str
    entity: str
    keywords: List[str]
    location: Optional[str]
    category: Optional[str]
    time_window_minutes: int
    status: str
    created_at: datetime
    summary: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
