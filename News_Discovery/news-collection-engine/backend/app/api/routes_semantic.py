from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import ArticleModel
from app.schemas.article import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultItem,
    ArticleRead
)
from app.services.qdrant_service import qdrant_service_instance
from app.services.deepseek_service import deepseek_service_instance
from app.utils.logger import get_logger

logger = get_logger("news_engine.routes_semantic")

router = APIRouter(prefix="/semantic", tags=["Semantic Discovery & AI Analysis"])


@router.get("/status")
def get_semantic_engine_status():
    """Returns real-time status of Qdrant Vector Database and DeepSeek-R1 AI Reasoning Engine."""
    return {
        "qdrant": qdrant_service_instance.get_status(),
        "deepseek_r1": deepseek_service_instance.get_status()
    }


@router.post("/search", response_model=SemanticSearchResponse)
def semantic_vector_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Executes semantic discovery search using Qdrant dense vector embeddings.
    Allows searching articles by natural language concept (e.g., 'EV charging breakthroughs').
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    qdrant_results = qdrant_service_instance.semantic_search(
        query=query_text,
        limit=request.limit,
        min_score=request.min_score,
        entity_filter=request.entity_filter
    )

    items = []
    for res in qdrant_results:
        try:
            art_id = res.get("id")
            # Fetch full DB article or construct ArticleRead from Qdrant payload
            db_art = db.query(ArticleModel).filter(ArticleModel.id == art_id).first()
            if db_art:
                art_read = ArticleRead.model_validate(db_art)
            else:
                art_read = ArticleRead(
                    id=art_id,
                    title=res.get("title", ""),
                    description=res.get("description", ""),
                    source=res.get("source", "Unknown"),
                    url=res.get("url", "#"),
                    target_entity=res.get("target_entity", "All Companies"),
                    relevance_score=res.get("relevance_score", 0.0),
                    importance_rating=res.get("importance_rating", "MEDIUM"),
                    sentiment_tone=res.get("sentiment_tone", "Neutral"),
                    ai_summary=res.get("ai_summary", ""),
                    reasoning_trace=res.get("reasoning_trace", ""),
                    published_at=res.get("published_at")
                )

            items.append(SemanticSearchResultItem(
                article=art_read,
                similarity_score=res.get("similarity_score", 0.0),
                score_percentage=res.get("score_percentage", 0)
            ))
        except Exception as e:
            logger.debug(f"Error mapping semantic search result item: {e}")

    # Fallback to database text search if Qdrant has not indexed points yet
    if not items:
        search_pattern = f"%{query_text}%"
        fallback_arts = db.query(ArticleModel).filter(
            ArticleModel.title.ilike(search_pattern) | ArticleModel.description.ilike(search_pattern)
        ).limit(request.limit).all()

        for a in fallback_arts:
            art_read = ArticleRead.model_validate(a)
            # Index into Qdrant for subsequent queries
            qdrant_service_instance.upsert_article(a)
            items.append(SemanticSearchResultItem(
                article=art_read,
                similarity_score=0.75,
                score_percentage=75
            ))

    return SemanticSearchResponse(
        query=query_text,
        total_found=len(items),
        results=items,
        vector_engine=f"Qdrant ({qdrant_service_instance.mode})"
    )


@router.get("/similar/{article_id}", response_model=List[SemanticSearchResultItem])
def get_similar_articles(
    article_id: str,
    limit: int = Query(default=4, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Retrieves semantically similar articles using Qdrant nearest-neighbor cosine similarity.
    """
    # Verify article exists
    art = db.query(ArticleModel).filter(ArticleModel.id == article_id).first()
    if not art:
        raise HTTPException(status_code=404, detail="Article not found")

    # Ensure this article is in Qdrant
    qdrant_service_instance.upsert_article(art)

    similar_results = qdrant_service_instance.find_similar_articles(
        article_id=article_id,
        limit=limit,
        min_score=0.35
    )

    items = []
    for res in similar_results:
        try:
            target_id = res.get("id")
            db_art = db.query(ArticleModel).filter(ArticleModel.id == target_id).first()
            if db_art:
                art_read = ArticleRead.model_validate(db_art)
            else:
                art_read = ArticleRead(
                    id=target_id,
                    title=res.get("title", ""),
                    description=res.get("description", ""),
                    source=res.get("source", "Unknown"),
                    url=res.get("url", "#"),
                    target_entity=res.get("target_entity", "All Companies"),
                    relevance_score=res.get("relevance_score", 0.0),
                    importance_rating=res.get("importance_rating", "MEDIUM"),
                    sentiment_tone=res.get("sentiment_tone", "Neutral"),
                    ai_summary=res.get("ai_summary", ""),
                    reasoning_trace=res.get("reasoning_trace", ""),
                    published_at=res.get("published_at")
                )

            items.append(SemanticSearchResultItem(
                article=art_read,
                similarity_score=res.get("similarity_score", 0.0),
                score_percentage=res.get("score_percentage", 0)
            ))
        except Exception as e:
            logger.debug(f"Error mapping similar article: {e}")

    # If Qdrant returns fewer than requested, fill with same entity or category
    if len(items) < limit:
        existing_ids = {article_id} | {item.article.id for item in items}
        fallback_query = db.query(ArticleModel).filter(
            ~ArticleModel.id.in_(existing_ids)
        )
        if art.target_entity and art.target_entity != "All Companies":
            fallback_query = fallback_query.filter(ArticleModel.target_entity == art.target_entity)

        extras = fallback_query.limit(limit - len(items)).all()
        for ex in extras:
            qdrant_service_instance.upsert_article(ex)
            items.append(SemanticSearchResultItem(
                article=ArticleRead.model_validate(ex),
                similarity_score=0.60,
                score_percentage=60
            ))

    return items


@router.post("/reindex")
def reindex_all_articles(db: Session = Depends(get_db)):
    """
    Indexes all existing articles from the database into Qdrant vector database.
    """
    articles = db.query(ArticleModel).all()
    count = qdrant_service_instance.bulk_upsert(articles)
    return {
        "status": "success",
        "total_articles_in_db": len(articles),
        "indexed_into_qdrant": count,
        "qdrant_status": qdrant_service_instance.get_status()
    }
