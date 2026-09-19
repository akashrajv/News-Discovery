import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from app.database.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    source_type = Column(String(32), nullable=False)  # API, RSS, AUTHORIZED_FEED
    connection_method = Column(String(32), nullable=False)  # api, rss, authorized_feed
    api_endpoint = Column(String(512), nullable=True)
    api_key_env_name = Column(String(64), nullable=True)
    api_key_configured = Column(Boolean, default=False)
    rss_url = Column(String(512), nullable=True)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=5)  # 1 (lowest) to 10 (highest)
    request_limit = Column(Integer, default=100)
    rate_limit_window_seconds = Column(Integer, default=86400)
    estimated_cost_per_request = Column(Float, default=0.0)
    last_successful_collection = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    requests_used = Column(Integer, default=0)
    requests_used_today = Column(Integer, default=0)
    requests_remaining = Column(Integer, default=100)
    last_reset_at = Column(DateTime, nullable=True)
    current_status = Column(String(32), default="AVAILABLE") # AVAILABLE, SELECTED, SKIPPED, RATE_LIMITED, FAILED, UNAVAILABLE
    retry_after = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CollectionRequestModel(Base):
    __tablename__ = "collection_requests"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    entity = Column(String(128), nullable=False)
    keywords = Column(JSON, nullable=False, default=list)
    location = Column(String(64), nullable=True)
    category = Column(String(64), nullable=True)
    time_window_minutes = Column(Integer, default=60)
    status = Column(String(32), default="pending")  # pending, success, partial_success, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(JSON, nullable=True)


class ArticleModel(Base):
    __tablename__ = "articles"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    source = Column(String(128), nullable=False)
    author = Column(String(256), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    url = Column(String(1024), nullable=False, unique=True, index=True)
    category = Column(String(64), nullable=True, index=True)
    location = Column(String(64), nullable=True)
    collection_method = Column(String(32), nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    image_url = Column(String(1024), nullable=True)
    dedup_hash = Column(String(64), nullable=True, unique=True, index=True)

    # Internal tracking
    canonical_url = Column(String(1024), nullable=True)
    normalized_title = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    source_id = Column(String(64), nullable=True)
    duplicate_group_id = Column(String(64), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    publication_time_unavailable = Column(Boolean, default=False)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

    # AI Semantic Intelligence fields
    target_entity = Column(String(128), nullable=True, index=True)
    relevance_score = Column(Float, default=0.0, index=True)
    importance_score = Column(Float, default=0.0)
    importance_rating = Column(String(32), default="MEDIUM", index=True)
    sentiment_tone = Column(String(32), default="Neutral")
    ai_summary = Column(Text, nullable=True)
    reasoning_trace = Column(Text, nullable=True)  # DeepSeek-R1 <think> reasoning chain
    qdrant_point_id = Column(String(64), nullable=True, index=True)  # Qdrant vector tracking point ID

    @property
    def fetched_at(self):
        return self.collected_at

    @property
    def content_snippet(self):
        return self.description


class DuplicateRelationshipModel(Base):
    __tablename__ = "duplicate_relationships"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    primary_article_id = Column(String(64), ForeignKey("articles.id"), nullable=False)
    duplicate_article_id = Column(String(64), ForeignKey("articles.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    detection_method = Column(String(64), nullable=False)  # canonical_url, normalized_url, normalized_title, content_hash, title_similarity
    created_at = Column(DateTime, default=datetime.utcnow)


class CacheMetadataModel(Base):
    __tablename__ = "cache_metadata"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    cache_key = Column(String(512), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)


class ApiUsageModel(Base):
    __tablename__ = "api_usage"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), nullable=False)
    source_name = Column(String(128), nullable=False)
    request_count = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)
    estimated_cost = Column(Float, default=0.0)
    status = Column(String(32), default="success")


class CollectionLogModel(Base):
    __tablename__ = "collection_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    request_id = Column(String(64), nullable=False)
    source_id = Column(String(64), nullable=True)
    source_name = Column(String(128), nullable=False)
    connector = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)  # success, skipped, rate_limited, failed
    articles_fetched = Column(Integer, default=0)
    articles_accepted = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    cache_hit_or_miss = Column(String(16), default="miss")  # hit, miss, bypass
    duration_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SourceErrorModel(Base):
    __tablename__ = "source_errors"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), nullable=False)
    source_name = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    error_type = Column(String(64), nullable=False)
    http_status = Column(Integer, nullable=True)
    message = Column(Text, nullable=False)
    retry_attempt = Column(Integer, default=0)
    recovery_status = Column(String(32), default="unresolved")
