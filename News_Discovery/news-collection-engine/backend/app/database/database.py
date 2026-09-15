import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("news_engine.database")

Base = declarative_base()

def get_engine(db_url: str):
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    
    try:
        engine = create_engine(db_url, connect_args=connect_args)
        # Verify connection
        with engine.connect() as conn:
            pass
        return engine, db_url
    except Exception as e:
        logger.warning(f"Failed to connect to database at '{db_url}': {e}. Falling back to SQLite.")
        fallback_url = "sqlite:///./news_engine.db"
        engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
        return engine, fallback_url

engine, ACTIVE_DATABASE_URL = get_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import text

def init_db():
    """Create all database tables and apply lightweight column migrations."""
    Base.metadata.create_all(bind=engine)
    
    # Check and add missing columns to SQLite table if needed
    try:
        with engine.begin() as conn:
            columns_res = conn.execute(text("PRAGMA table_info(articles)")).fetchall()
            col_names = {row[1] for row in columns_res} if columns_res else set()

            if col_names:
                if "image_url" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN image_url VARCHAR(1024)"))
                if "dedup_hash" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN dedup_hash VARCHAR(64)"))
                if "target_entity" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN target_entity VARCHAR(255) DEFAULT 'All Companies'"))
                if "relevance_score" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN relevance_score FLOAT DEFAULT 0.0"))
                if "importance_score" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN importance_score FLOAT DEFAULT 0.0"))
                if "importance_rating" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN importance_rating VARCHAR(32) DEFAULT 'MEDIUM'"))
                if "sentiment_tone" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN sentiment_tone VARCHAR(64) DEFAULT 'Neutral'"))
                if "ai_summary" not in col_names:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN ai_summary TEXT"))

            sources_cols_res = conn.execute(text("PRAGMA table_info(sources)")).fetchall()
            src_col_names = {row[1] for row in sources_cols_res} if sources_cols_res else set()
            if src_col_names:
                if "requests_used_today" not in src_col_names:
                    conn.execute(text("ALTER TABLE sources ADD COLUMN requests_used_today INTEGER DEFAULT 0"))
                if "last_reset_at" not in src_col_names:
                    conn.execute(text("ALTER TABLE sources ADD COLUMN last_reset_at DATETIME"))
    except Exception as err:
        logger.warning(f"Database column migration note: {err}")

