from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.database import init_db, SessionLocal
from app.registry.source_registry import SourceRegistry
from app.utils.logger import get_logger

from app.api.routes_collect import router as collect_router
from app.api.routes_articles import router as articles_router
from app.api.routes_sources import router as sources_router
from app.api.routes_usage import router as usage_router
from app.api.routes_history import router as history_router
from app.api.routes_health import router as health_router
from app.api.routes_cache import router as cache_router
from app.api.routes_routing import router as routing_router

from app.services.scheduler_service import scheduler_service
from app.database.mongodb import mongo_manager

logger = get_logger("news_engine.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema & seed default sources...")
    init_db()

    # Connect to MongoDB cluster if configured
    if settings.MONGODB_URL:
        logger.info("Connecting to MongoDB cluster...")
        mongo_manager.connect()

    db = SessionLocal()
    try:
        SourceRegistry.initialize_default_sources(db)
        # Backfill relevance score for any legacy/unscored articles
        from app.database.models import ArticleModel
        from app.services.relevance_service import RelevanceService
        unscored = db.query(ArticleModel).filter(
            (ArticleModel.relevance_score == 0.0) | (ArticleModel.relevance_score.is_(None))
        ).all()
        if unscored:
            logger.info(f"Backfilling AI semantic relevance scores for {len(unscored)} stored articles...")
            for art in unscored:
                target = art.target_entity or "All Companies"
                analysis = RelevanceService.compute_semantic_analysis(
                    title=art.title,
                    description=art.description,
                    content=art.content,
                    target_entity=target
                )
                art.target_entity = analysis["target_entity"]
                art.relevance_score = analysis["relevance_score"]
                art.importance_score = analysis["importance_score"]
                art.importance_rating = analysis["importance_rating"]
                art.sentiment_tone = analysis["sentiment_tone"]
                art.ai_summary = analysis["ai_summary"]
            db.commit()
    finally:
        db.close()
    
    # Start background scheduler for periodic news fetch & retention cleanup
    scheduler_service.start()

    logger.info(f"{settings.APP_NAME} started successfully (DEMO_MODE={settings.DEMO_MODE}).")
    yield
    logger.info("Shutting down application & scheduler...")
    scheduler_service.shutdown()
    mongo_manager.close()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Modular Multi-Source News Collection Engine for AI News Intelligence Platforms.",
    lifespan=lifespan
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(collect_router)
app.include_router(articles_router)
app.include_router(sources_router)
app.include_router(usage_router)
app.include_router(history_router)
app.include_router(health_router)
app.include_router(cache_router)
app.include_router(routing_router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "demo_mode": settings.DEMO_MODE,
        "documentation": "/docs"
    }
