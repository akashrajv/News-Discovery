import re
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymongo
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel, UpdateOne
from pymongo.errors import PyMongoError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("news_engine.mongodb")


def sanitize_mongodb_uri(uri: str) -> str:
    """
    Sanitize and URL-encode credentials in a MongoDB connection string.
    Handles unescaped '@' characters or '<password>' placeholders in user/pass.
    """
    if not uri or not uri.strip():
        return ""
    uri = uri.strip()

    if "://" not in uri:
        return uri

    proto, rest = uri.split("://", 1)
    if not proto.startswith("mongodb"):
        return uri

    # Find where the authority ends (at first '/' or '?')
    delims = [i for i in [rest.find("/"), rest.find("?")] if i != -1]
    split_idx = min(delims) if delims else len(rest)

    authority = rest[:split_idx]
    path_and_query = rest[split_idx:]

    # The last '@' in authority separates userinfo from the host:port
    at_idx = authority.rfind("@")
    if at_idx == -1:
        return uri

    creds = authority[:at_idx]
    host = authority[at_idx + 1:]

    # Check if there are user:pass
    if ":" in creds:
        user, password = creds.split(":", 1)

        # Strip surrounding < and > if present
        if password.startswith("<") and password.endswith(">"):
            password = password[1:-1]
        if user.startswith("<") and user.endswith(">"):
            user = user[1:-1]

        # Decode first if already partially percent-encoded, then encode cleanly
        user = urllib.parse.unquote_plus(user)
        password = urllib.parse.unquote_plus(password)

        clean_user = urllib.parse.quote_plus(user)
        clean_pass = urllib.parse.quote_plus(password)

        return f"{proto}://{clean_user}:{clean_pass}@{host}{path_and_query}"

    return uri


class MongoDBManager:
    """Manager for MongoDB client connection, article collections, and queries."""

    def __init__(self):
        self.client: Optional[pymongo.MongoClient] = None
        self.db = None
        self.is_connected: bool = False
        self.connection_error: Optional[str] = None
        self.db_name: str = settings.MONGODB_DB_NAME

    def connect(self) -> bool:
        """Establish connection to MongoDB cluster."""
        raw_uri = settings.MONGODB_URL
        if not raw_uri:
            logger.info("MongoDB URL is not configured. MongoDB storage is disabled.")
            self.is_connected = False
            self.connection_error = "MONGODB_URL not configured"
            return False

        sanitized_uri = sanitize_mongodb_uri(raw_uri)
        try:
            logger.info("Connecting to MongoDB cluster...")
            client_kwargs: Dict[str, Any] = {
                "serverSelectionTimeoutMS": 2000,
                "connectTimeoutMS": 2000,
                "socketTimeoutMS": 3000,
                "appname": "NewsDiscoveryEngine",
            }
            try:
                import certifi
                client_kwargs["tlsCAFile"] = certifi.where()
            except Exception:
                pass

            self.client = pymongo.MongoClient(
                sanitized_uri,
                **client_kwargs
            )
            # Verify connectivity via ping
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.is_connected = True
            self.connection_error = None
            logger.info(f"Successfully connected to MongoDB database '{self.db_name}'")

            # Initialize indexes
            self.init_indexes()
            return True
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)
            logger.warning(f"MongoDB connection failed: {e}. Falling back to relational storage.")
            return False

    def close(self):
        """Close MongoDB client connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.is_connected = False

    def init_indexes(self):
        """Create high-performance indexes on articles collection."""
        if not self.is_connected or self.db is None:
            return

        try:
            articles_col = self.db.articles
            indexes = [
                # Unique URL index
                IndexModel([("url", ASCENDING)], unique=True, name="idx_unique_url"),
                # Sparse dedup hash index
                IndexModel([("dedup_hash", ASCENDING)], sparse=True, name="idx_dedup_hash"),
                # Published timestamp for recency sorting
                IndexModel([("published_at", DESCENDING)], name="idx_published_at"),
                # Collected timestamp
                IndexModel([("collected_at", DESCENDING)], name="idx_collected_at"),
                # Compound entity + relevance
                IndexModel([("target_entity", ASCENDING), ("relevance_score", DESCENDING)], name="idx_entity_relevance"),
                # Source and Category indexes
                IndexModel([("category", ASCENDING)], name="idx_category"),
                IndexModel([("source", ASCENDING)], name="idx_source"),
                IndexModel([("importance_rating", ASCENDING)], name="idx_importance_rating"),
                # Full-text search index on title & description
                IndexModel([("title", TEXT), ("description", TEXT)], name="idx_text_search"),
            ]
            articles_col.create_indexes(indexes)
            logger.info("MongoDB article collection indexes successfully ensured.")
        except Exception as e:
            logger.warning(f"Note: MongoDB index creation resulted in: {e}")

    def clean_doc_for_return(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document (_id, etc.) to format expected by ArticleRead."""
        if not doc:
            return {}
        doc = dict(doc)
        if "_id" in doc:
            mongo_id = str(doc.pop("_id"))
            if not doc.get("id"):
                doc["id"] = mongo_id

        # Normalize datetimes if stored as string or datetime
        now = datetime.utcnow()
        for dt_field in ["published_at", "collected_at", "first_seen_at", "last_seen_at"]:
            val = doc.get(dt_field)
            if isinstance(val, str):
                try:
                    doc[dt_field] = datetime.fromisoformat(val.replace("Z", "+00:00"))
                except Exception:
                    doc[dt_field] = now

        if not doc.get("first_seen_at"):
            doc["first_seen_at"] = doc.get("collected_at") or now
        if not doc.get("last_seen_at"):
            doc["last_seen_at"] = now
        if not doc.get("collected_at"):
            doc["collected_at"] = now

        return doc

    def upsert_article(self, article_data: Dict[str, Any]) -> bool:
        """Upsert a single article by url or dedup_hash."""
        if not self.is_connected or self.db is None:
            return False

        try:
            now = datetime.utcnow()
            doc = dict(article_data)
            url = doc.get("url")
            dedup_hash = doc.get("dedup_hash")

            if not url:
                return False

            filter_query = {"url": url}
            if dedup_hash:
                filter_query = {"$or": [{"url": url}, {"dedup_hash": dedup_hash}]}

            update_doc = {
                "$set": {
                    k: v for k, v in doc.items() if k not in ["_id", "first_seen_at"]
                },
                "$setOnInsert": {
                    "first_seen_at": doc.get("first_seen_at") or now,
                },
            }
            # Always refresh last_seen_at
            update_doc["$set"]["last_seen_at"] = now

            self.db.articles.update_one(filter_query, update_doc, upsert=True)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert article to MongoDB: {e}")
            return False

    def bulk_upsert_articles(self, articles: List[Dict[str, Any]]) -> int:
        """Bulk upsert articles into MongoDB using bulk_write."""
        if not self.is_connected or self.db is None or not articles:
            return 0

        now = datetime.utcnow()
        operations = []

        for item in articles:
            doc = dict(item)
            url = doc.get("url")
            dedup_hash = doc.get("dedup_hash")

            if not url:
                continue

            filter_q = {"url": url}
            if dedup_hash:
                filter_q = {"$or": [{"url": url}, {"dedup_hash": dedup_hash}]}

            set_fields = {k: v for k, v in doc.items() if k not in ["_id", "first_seen_at"]}
            set_fields["last_seen_at"] = now

            op = UpdateOne(
                filter_q,
                {
                    "$set": set_fields,
                    "$setOnInsert": {
                        "first_seen_at": doc.get("first_seen_at") or now,
                    },
                },
                upsert=True,
            )
            operations.append(op)

        if not operations:
            return 0

        try:
            result = self.db.articles.bulk_write(operations, ordered=False)
            upserted_or_modified = (result.upserted_count or 0) + (result.modified_count or 0)
            logger.info(
                f"MongoDB bulk write: {result.upserted_count} inserted, {result.modified_count} updated."
            )
            return upserted_or_modified
        except Exception as e:
            logger.error(f"MongoDB bulk_write partial failure: {e}")
            return 0

    def get_articles(
        self,
        category: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        entity: Optional[str] = None,
        min_relevance: Optional[float] = None,
        importance: Optional[str] = None,
        sort_by: str = "published_at",
        order: str = "desc",
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query articles with filters, search, sorting, and pagination from MongoDB."""
        if not self.is_connected or self.db is None:
            return [], 0

        query_filter: Dict[str, Any] = {}

        if category:
            query_filter["category"] = category
        if source:
            query_filter["source"] = source
        if min_relevance is not None:
            query_filter["relevance_score"] = {"$gte": float(min_relevance)}
        if importance:
            query_filter["importance_rating"] = {"$regex": f"^{importance.strip()}$", "$options": "i"}

        # Entity filter
        if entity and entity.strip().lower() not in ["all", "all companies"]:
            clean_entity = entity.strip()
            query_filter["$or"] = [
                {"target_entity": {"$regex": clean_entity, "$options": "i"}},
                {"title": {"$regex": clean_entity, "$options": "i"}},
                {"description": {"$regex": clean_entity, "$options": "i"}},
            ]

        # Search filter
        if search:
            search_regex = {"$regex": search.strip(), "$options": "i"}
            search_conditions = [
                {"title": search_regex},
                {"description": search_regex},
                {"source": search_regex},
            ]
            if "$or" in query_filter:
                query_filter = {"$and": [query_filter, {"$or": search_conditions}]}
            else:
                query_filter["$or"] = search_conditions

        # Sort order
        sort_direction = DESCENDING if order.lower() == "desc" else ASCENDING
        sort_field = sort_by if sort_by in [
            "published_at",
            "collected_at",
            "title",
            "relevance_score",
            "importance_score",
        ] else "published_at"

        try:
            total_count = self.db.articles.count_documents(query_filter)
            cursor = (
                self.db.articles.find(query_filter)
                .sort(sort_field, sort_direction)
                .skip(offset)
                .limit(limit)
            )

            articles = [self.clean_doc_for_return(doc) for doc in cursor]
            return articles, total_count
        except Exception as e:
            logger.error(f"Error querying articles from MongoDB: {e}")
            return [], 0

    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single article by ID or _id from MongoDB."""
        if not self.is_connected or self.db is None:
            return None

        try:
            doc = self.db.articles.find_one({"id": article_id})
            if not doc:
                # Try ObjectId if valid
                from bson import ObjectId

                if ObjectId.is_valid(article_id):
                    doc = self.db.articles.find_one({"_id": ObjectId(article_id)})

            return self.clean_doc_for_return(doc) if doc else None
        except Exception as e:
            logger.error(f"Error retrieving article {article_id} from MongoDB: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Diagnostic status for health checks."""
        if not settings.MONGODB_URL:
            return {
                "configured": False,
                "status": "unconfigured",
                "message": "Set MONGODB_URL in .env to enable MongoDB article storage",
            }

        if self.is_connected and self.db is not None:
            try:
                count = self.db.articles.count_documents({})
                return {
                    "configured": True,
                    "status": "connected",
                    "database": self.db_name,
                    "articles_count": count,
                }
            except Exception as e:
                return {
                    "configured": True,
                    "status": "degraded",
                    "database": self.db_name,
                    "error": str(e),
                }

        return {
            "configured": True,
            "status": "auth_or_connection_error",
            "database": self.db_name,
            "error": self.connection_error,
        }


# Singleton instance for application
mongo_manager = MongoDBManager()
