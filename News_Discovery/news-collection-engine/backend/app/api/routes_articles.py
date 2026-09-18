import math
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.config import settings
from app.database.database import get_db
from app.database.models import ArticleModel
from app.database.mongodb import mongo_manager
from app.schemas.article import ArticleRead, PaginatedArticlesRead
from app.services.relevance_service import RelevanceService
from app.utils.logger import get_logger

logger = get_logger("news_engine.routes_articles")

router = APIRouter(prefix="/api/articles", tags=["Articles"])

@router.get("", response_model=Union[PaginatedArticlesRead, List[ArticleRead]])
def get_articles(
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    min_relevance: Optional[float] = Query(None, ge=0.0, le=100.0),
    importance: Optional[str] = Query(None),
    page: Optional[int] = Query(None, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: Optional[int] = Query(None, ge=0),
    sort_by: str = Query("published_at", pattern="^(published_at|collected_at|title|relevance_score|importance_score)$"),
    order: str = Query("desc", pattern="^(desc|asc)$"),
    paginated: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Retrieve cached articles directly from MongoDB (or relational database fallback)
    with pagination, filtering, and sorting.
    Does NOT call external APIs on read requests.
    """
    # Determine pagination/offset
    if page is not None:
        effective_page = page
        effective_page_size = page_size
        effective_offset = (effective_page - 1) * effective_page_size
    else:
        effective_page = 1
        effective_page_size = limit or page_size
        effective_offset = offset or 0

    # Primary storage: If MongoDB is connected and enabled, query MongoDB
    if mongo_manager.is_connected and settings.ARTICLE_STORAGE_BACKEND in ["mongodb", "both"]:
        try:
            mongo_articles, total_count = mongo_manager.get_articles(
                category=category,
                source=source,
                search=search,
                entity=entity,
                min_relevance=min_relevance,
                importance=importance,
                sort_by=sort_by,
                order=order,
                offset=effective_offset,
                limit=effective_page_size,
            )
            # If MongoDB has articles, return them
            if total_count > 0:
                articles_read = [ArticleRead.model_validate(doc) for doc in mongo_articles]
                if paginated or page is not None:
                    total_pages = math.ceil(total_count / effective_page_size) if effective_page_size > 0 else 1
                    return PaginatedArticlesRead(
                        total=total_count,
                        page=effective_page,
                        page_size=effective_page_size,
                        total_pages=total_pages,
                        articles=articles_read
                    )
                return articles_read
        except Exception as mongo_err:
            logger.warning(f"MongoDB query failed, falling back to SQL: {mongo_err}")

    # Fallback to Relational Database
    query = db.query(ArticleModel)

    if category:
        query = query.filter(ArticleModel.category == category)
    if source:
        query = query.filter(ArticleModel.source == source)
    if entity and entity.strip().lower() not in ["all", "all companies"]:
        entity_pattern = f"%{entity.strip()}%"
        query = query.filter(
            or_(
                ArticleModel.target_entity.ilike(entity_pattern),
                ArticleModel.title.ilike(entity_pattern),
                ArticleModel.description.ilike(entity_pattern)
            )
        )
    if min_relevance is not None:
        query = query.filter(ArticleModel.relevance_score >= min_relevance)
    if importance:
        query = query.filter(ArticleModel.importance_rating.ilike(importance.strip()))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                ArticleModel.title.ilike(search_pattern),
                ArticleModel.description.ilike(search_pattern),
                ArticleModel.source.ilike(search_pattern)
            )
        )

    # Sorting
    sort_attr = getattr(ArticleModel, sort_by, ArticleModel.published_at)
    if order.lower() == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    total_count = query.count()

    # Determine pagination/offset
    if page is not None:
        effective_page = page
        effective_page_size = page_size
        effective_offset = (effective_page - 1) * effective_page_size
    else:
        effective_page = 1
        effective_page_size = limit or page_size
        effective_offset = offset or 0

    articles = query.offset(effective_offset).limit(effective_page_size).all()

    for a in articles:
        if a.relevance_score == 0.0 or a.relevance_score is None:
            target = entity if (entity and entity.strip().lower() not in ["all", "all companies"]) else (a.target_entity or "All Companies")
            analysis = RelevanceService.compute_semantic_analysis(
                title=a.title,
                description=a.description,
                content=a.content,
                target_entity=target
            )
            a.target_entity = analysis["target_entity"]
            a.relevance_score = analysis["relevance_score"]
            a.importance_score = analysis["importance_score"]
            a.importance_rating = analysis["importance_rating"]
            a.sentiment_tone = analysis["sentiment_tone"]
            a.ai_summary = analysis["ai_summary"]

    articles_read = [ArticleRead.model_validate(a) for a in articles]

    if paginated or page is not None:
        import math
        total_pages = math.ceil(total_count / effective_page_size) if effective_page_size > 0 else 1
        return PaginatedArticlesRead(
            total=total_count,
            page=effective_page,
            page_size=effective_page_size,
            total_pages=total_pages,
            articles=articles_read
        )

    return articles_read

@router.get("/{article_id}", response_model=ArticleRead)
def get_article_by_id(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve single article by ID from MongoDB or relational database fallback."""
    if mongo_manager.is_connected and settings.ARTICLE_STORAGE_BACKEND in ["mongodb", "both"]:
        try:
            doc = mongo_manager.get_article_by_id(article_id)
            if doc:
                return ArticleRead.model_validate(doc)
        except Exception as mongo_err:
            logger.warning(f"Failed to fetch article {article_id} from MongoDB, falling back to SQL: {mongo_err}")

    article = db.query(ArticleModel).filter(ArticleModel.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleRead.model_validate(article)
