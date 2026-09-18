import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import (
    CollectionRequestModel, ArticleModel, DuplicateRelationshipModel,
    CollectionLogModel, SourceModel
)
from app.schemas.collection import CollectionRequestInput, CollectionResponse
from app.schemas.article import ArticleRead
from app.registry.source_registry import SourceRegistry
from app.router.source_router import SourceRouter
from app.services.recency_service import RecencyService
from app.services.deduplication_service import DeduplicationService
from app.services.cache_service import cache_service_instance, CacheService
from app.services.rate_limit_service import RateLimitService
from app.services.cost_service import CostService
from app.services.relevance_service import RelevanceService
from app.services.demo_service import get_demo_articles
from app.database.mongodb import mongo_manager
from app.utils.logger import get_logger

logger = get_logger("news_engine.collection_service")

class CollectionService:
    """Core Orchestrator for the Multi-Source News Collection Engine."""

    def __init__(self, db: Session):
        self.db = db
        self.router = SourceRouter(db)

    async def execute_collection(self, request_input: CollectionRequestInput) -> CollectionResponse:
        request_id = f"req_{uuid.uuid4().hex[:10]}"

        # Resolve entity list (supports single entity, comma-separated entities, or list)
        entity_list = []
        if request_input.entities:
            entity_list = [e.strip() for e in request_input.entities if e.strip()]
        elif request_input.entity:
            entity_list = [e.strip() for e in request_input.entity.split(",") if e.strip()]

        primary_entity_label = ", ".join(entity_list) if entity_list else (request_input.entity or "All Companies")
        logger.info(f"Starting news collection [{request_id}] for entities: '{primary_entity_label}'")

        # 1. Generate Cache Key
        cache_key = CacheService.generate_cache_key(
            entity=primary_entity_label,
            keywords=request_input.keywords,
            location=request_input.location,
            category=request_input.category,
            time_window_minutes=request_input.time_window_minutes
        )

        # 2. Check Cache
        cached_data = cache_service_instance.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached payload for {request_id}")
            req_record = CollectionRequestModel(
                id=request_id,
                entity=primary_entity_label,
                keywords=request_input.keywords,
                location=request_input.location,
                category=request_input.category,
                time_window_minutes=request_input.time_window_minutes,
                status="success",
                summary={"cache_hit": True}
            )
            self.db.add(req_record)
            self.db.commit()

            routing_eval = self.router.evaluate_routing(
                request_id=request_id,
                entity=primary_entity_label,
                cache_hit=True,
                demo_mode=settings.DEMO_MODE
            )

            articles_read = [ArticleRead.model_validate(a) for a in cached_data.get("articles", [])]

            return CollectionResponse(
                status="success",
                request_id=request_id,
                articles_collected=len(articles_read),
                duplicates_removed=cached_data.get("duplicates_removed", 0),
                cache_hits=1,
                cache_misses=0,
                sources_used=0,
                sources_failed=0,
                api_requests=0,
                rss_collections=0,
                estimated_api_cost=0.0,
                articles=articles_read,
                routing_summary=routing_eval.model_dump(),
                demo_mode=settings.DEMO_MODE,
                message="Retrieved from cache (0 source requests required)"
            )

        # 3. Source Selection & Routing
        routing_eval = self.router.evaluate_routing(
            request_id=request_id,
            entity=primary_entity_label,
            cache_hit=False,
            demo_mode=settings.DEMO_MODE
        )

        raw_articles = []
        sources_used = 0
        sources_failed = 0
        api_requests = 0
        rss_collections = 0
        total_estimated_cost = 0.0

        demo_articles_pool = get_demo_articles(primary_entity_label, request_input.keywords) if settings.DEMO_MODE else []

        # 4. Fetch Articles from Selected Sources
        for source_decision in routing_eval.selected_sources:
            source_id = source_decision.source_id
            start_time = time.time()

            source_model = self.db.query(SourceModel).filter(SourceModel.id == source_id).first()
            if not source_model:
                continue

            connector = SourceRegistry.get_connector(source_model)
            query = connector.build_query(
                entity=primary_entity_label,
                keywords=request_input.keywords,
                location=request_input.location,
                category=request_input.category
            )

            try:
                if settings.DEMO_MODE:
                    # Simulated collection per source
                    source_demo_articles = [a for a in demo_articles_pool if a.source_id == source_id]
                    fetched_count = len(source_demo_articles)
                    raw_articles.extend(source_demo_articles)
                    status_str = "success"
                else:
                    # Live connector fetch
                    is_allowed, rate_msg, _ = RateLimitService.check_rate_limit(self.db, source_id)
                    if not is_allowed:
                        logger.warning(f"Source {source_model.name} rate limited: {rate_msg}")
                        sources_failed += 1
                        continue

                    fetched_items = await RateLimitService.execute_with_retry(
                        connector.fetch, query, request_input.time_window_minutes
                    )
                    normalized_items = connector.normalize(fetched_items)
                    fetched_count = len(normalized_items)
                    raw_articles.extend(normalized_items)
                    status_str = "success"

                duration_ms = round((time.time() - start_time) * 1000, 2)
                sources_used += 1

                if source_model.connection_method == "api":
                    api_requests += 1
                    cost = source_model.estimated_cost_per_request
                    total_estimated_cost += cost
                    CostService.record_api_usage(self.db, source_id, source_model.name, 1, cost)
                elif source_model.connection_method == "rss":
                    rss_collections += 1

                RateLimitService.record_request_used(self.db, source_id, success=True)

                # Log collection attempt
                log_entry = CollectionLogModel(
                    request_id=request_id,
                    source_id=source_id,
                    source_name=source_model.name,
                    connector=source_model.connection_method,
                    status=status_str,
                    articles_fetched=fetched_count,
                    articles_accepted=fetched_count,
                    cache_hit_or_miss="miss",
                    duration_ms=duration_ms
                )
                self.db.add(log_entry)

            except Exception as e:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                logger.error(f"Error collecting from {source_model.name}: {e}")
                sources_failed += 1
                RateLimitService.record_request_used(self.db, source_id, success=False, error_msg=str(e))

                log_entry = CollectionLogModel(
                    request_id=request_id,
                    source_id=source_id,
                    source_name=source_model.name,
                    connector=source_model.connection_method,
                    status="failed",
                    articles_fetched=0,
                    articles_accepted=0,
                    cache_hit_or_miss="miss",
                    duration_ms=duration_ms,
                    error_message=str(e)
                )
                self.db.add(log_entry)

        # 5. Recency Filtering
        retained_articles, filtered_recency_count = RecencyService.filter_by_recency(
            raw_articles, time_window_minutes=request_input.time_window_minutes
        )

        # 5.5 AI Semantic Relevance Filtering & Enrichment
        semantically_filtered = []
        for art in retained_articles:
            analysis = RelevanceService.compute_semantic_analysis(
                title=art.title,
                description=art.description,
                content=art.content,
                target_entity=primary_entity_label,
                keywords=request_input.keywords
            )
            art.target_entity = analysis["target_entity"]
            art.relevance_score = analysis["relevance_score"]
            art.importance_score = analysis["importance_score"]
            art.importance_rating = analysis["importance_rating"]
            art.sentiment_tone = analysis["sentiment_tone"]
            art.ai_summary = analysis["ai_summary"]

            # Filter out articles below 30% relevance when a specific entity is requested
            if primary_entity_label and primary_entity_label.lower() not in ["all", "all companies"] and analysis["relevance_score"] < 30.0:
                continue
            semantically_filtered.append(art)

        # 6. Multi-Stage Deduplication across all collected articles
        unique_articles, duplicate_relationships = DeduplicationService.deduplicate(
            semantically_filtered, similarity_threshold=0.85
        )

        duplicates_removed = len(duplicate_relationships)

        # 7. Store Unique Articles and Duplicate Mapping in Database
        db_articles = []
        for article in unique_articles:
            art_model = ArticleModel(
                title=article.title,
                description=article.description,
                content=article.content,
                source=article.source,
                author=getattr(article, "author", None),
                published_at=article.published_at,
                url=article.url,
                category=request_input.category or article.category,
                location=request_input.location or article.location,
                collection_method=article.collection_method,
                canonical_url=article.canonical_url,
                normalized_title=article.normalized_title,
                content_hash=article.content_hash,
                source_id=article.source_id,
                publication_time_unavailable=article.publication_time_unavailable,
                target_entity=getattr(article, "target_entity", primary_entity_label),
                relevance_score=getattr(article, "relevance_score", 85.0),
                importance_score=getattr(article, "importance_score", 50.0),
                importance_rating=getattr(article, "importance_rating", "MEDIUM"),
                sentiment_tone=getattr(article, "sentiment_tone", "Neutral"),
                ai_summary=getattr(article, "ai_summary", None)
            )
            self.db.add(art_model)
            db_articles.append(art_model)

        self.db.flush()

        # Save Duplicate Relationships
        for dup in duplicate_relationships:
            p_art = next((a for a in db_articles if a.title == dup["primary_article_title"]), None)
            if p_art:
                dup_rel = DuplicateRelationshipModel(
                    primary_article_id=p_art.id,
                    duplicate_article_id=p_art.id,
                    similarity_score=dup["similarity_score"],
                    detection_method=dup["detection_method"]
                )
                self.db.add(dup_rel)

        # 8. Record Collection Request
        overall_status = "success"
        if sources_used > 0 and sources_failed > 0:
            overall_status = "partial_success"
        elif sources_used == 0 and sources_failed > 0:
            overall_status = "failed"

        req_record = CollectionRequestModel(
            id=request_id,
            entity=primary_entity_label,
            keywords=request_input.keywords,
            location=request_input.location,
            category=request_input.category,
            time_window_minutes=request_input.time_window_minutes,
            status=overall_status,
            summary={
                "articles_collected": len(db_articles),
                "duplicates_removed": duplicates_removed,
                "sources_used": sources_used,
                "sources_failed": sources_failed,
                "estimated_api_cost": round(total_estimated_cost, 4)
            }
        )
        self.db.add(req_record)
        self.db.commit()

        # Dual-storage: Persist to MongoDB if connected or configured
        if mongo_manager.is_connected:
            try:
                mongo_docs = []
                for a in db_articles:
                    mongo_docs.append({
                        "id": str(a.id),
                        "title": a.title,
                        "description": a.description,
                        "content": a.content,
                        "source": a.source,
                        "author": a.author,
                        "published_at": a.published_at,
                        "url": a.url,
                        "category": a.category,
                        "location": a.location,
                        "collection_method": a.collection_method,
                        "collected_at": a.collected_at,
                        "canonical_url": a.canonical_url,
                        "normalized_title": a.normalized_title,
                        "content_hash": a.content_hash,
                        "dedup_hash": a.dedup_hash,
                        "source_id": a.source_id,
                        "target_entity": a.target_entity,
                        "relevance_score": a.relevance_score,
                        "importance_score": a.importance_score,
                        "importance_rating": a.importance_rating,
                        "sentiment_tone": a.sentiment_tone,
                        "ai_summary": a.ai_summary,
                        "image_url": getattr(a, "image_url", None),
                    })
                if mongo_docs:
                    mongo_manager.bulk_upsert_articles(mongo_docs)
            except Exception as mongo_err:
                logger.warning(f"Error syncing articles to MongoDB: {mongo_err}")

        articles_read = [ArticleRead.model_validate(a) for a in db_articles]

        # 9. Store Result in Cache
        cache_payload = {
            "articles": [a.model_dump() for a in articles_read],
            "duplicates_removed": duplicates_removed,
            "sources_used": sources_used,
            "estimated_api_cost": round(total_estimated_cost, 4)
        }
        cache_service_instance.set(cache_key, cache_payload)

        logger.info(f"Collection [{request_id}] completed: {len(articles_read)} articles, {duplicates_removed} duplicates removed")

        return CollectionResponse(
            status=overall_status,
            request_id=request_id,
            articles_collected=len(articles_read),
            duplicates_removed=duplicates_removed,
            cache_hits=0,
            cache_misses=1,
            sources_used=sources_used,
            sources_failed=sources_failed,
            api_requests=api_requests,
            rss_collections=rss_collections,
            estimated_api_cost=round(total_estimated_cost, 4),
            articles=articles_read,
            routing_summary=routing_eval.model_dump(),
            demo_mode=settings.DEMO_MODE,
            message="Collection completed successfully"
        )
