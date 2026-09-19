from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    url: str
    category: Optional[str] = None
    location: Optional[str] = None
    collection_method: str = "api"
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    image_url: Optional[str] = None
    dedup_hash: Optional[str] = None
    
    # AI Semantic Intelligence fields
    target_entity: Optional[str] = "All Companies"
    relevance_score: Optional[float] = 0.0
    importance_score: Optional[float] = 0.0
    importance_rating: Optional[str] = "MEDIUM"
    sentiment_tone: Optional[str] = "Neutral"
    ai_summary: Optional[str] = None
    reasoning_trace: Optional[str] = None  # DeepSeek-R1 <think> reasoning chain
    qdrant_point_id: Optional[str] = None  # Qdrant vector tracking point ID

class ArticleCreate(ArticleBase):
    canonical_url: Optional[str] = None
    normalized_title: Optional[str] = None
    content_hash: Optional[str] = None
    source_id: Optional[str] = None
    publication_time_unavailable: bool = False

class ArticleRead(ArticleBase):
    id: str
    canonical_url: Optional[str] = None
    normalized_title: Optional[str] = None
    content_hash: Optional[str] = None
    source_id: Optional[str] = None
    duplicate_group_id: Optional[str] = None
    is_duplicate: bool = False
    publication_time_unavailable: bool = False
    first_seen_at: datetime
    last_seen_at: datetime
    content_snippet: Optional[str] = None
    fetched_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedArticlesRead(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    articles: List[ArticleRead]

class DuplicateRelationshipRead(BaseModel):
    id: str
    primary_article_id: str
    duplicate_article_id: str
    similarity_score: float
    detection_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language semantic search query")
    limit: int = Field(default=10, ge=1, le=50, description="Max results to return")
    min_score: float = Field(default=0.4, ge=0.0, le=1.0, description="Minimum cosine similarity score")
    entity_filter: Optional[str] = Field(default=None, description="Optional target entity filter")

class SemanticSearchResultItem(BaseModel):
    article: ArticleRead
    similarity_score: float
    score_percentage: int

class SemanticSearchResponse(BaseModel):
    query: str
    total_found: int
    results: List[SemanticSearchResultItem]
    vector_engine: str = "Qdrant"
