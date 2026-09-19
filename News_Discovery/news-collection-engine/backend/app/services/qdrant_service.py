import os
import re
import math
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("news_engine.qdrant_service")


class SemanticVectorizer:
    """
    Lightweight, deterministic dense semantic vectorizer (dimension: 384).
    Computes normalized semantic embeddings based on character/word n-grams,
    subwords, and domain semantic keywords to ensure zero external dependency
    download latency while providing accurate cosine similarity rankings.
    """
    DIMENSION = 384

    # Salient semantic anchor terms that project onto distinct orthogonal dimensions
    ANCHOR_DOMAINS = [
        "ai", "artificial intelligence", "deep learning", "machine learning", "gpu", "chip", "semiconductor",
        "nvidia", "blackwell", "hopper", "cuda", "supercomputer", "data center", "cloud",
        "ev", "electric vehicle", "battery", "tesla", "robotaxi", "cybercab", "autopilot", "fsd",
        "tata motors", "nexon", "jlr", "automaker", "automotive", "car sales", "suv",
        "apple", "iphone", "macbook", "m3", "m4", "apple intelligence", "ios", "vision pro",
        "microsoft", "azure", "copilot", "windows", "openai", "chatgpt", "sam altman", "llm",
        "earnings", "revenue", "profit", "quarterly", "growth", "record", "acquisition", "merger",
        "lawsuit", "investigation", "antitrust", "recall", "regulatory", "layoffs", "breach"
    ]

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        """Generate a unit-normalized 384-dimensional dense vector for input text."""
        if not text:
            vec = np.zeros(cls.DIMENSION, dtype=np.float32)
            vec[0] = 1.0
            return vec.tolist()

        text_lower = text.lower().strip()
        vec = np.zeros(cls.DIMENSION, dtype=np.float32)

        # 1. Project Domain Semantic Anchors (Dimensions 0 to 63)
        num_anchors = min(len(cls.ANCHOR_DOMAINS), 64)
        for i in range(num_anchors):
            anchor = cls.ANCHOR_DOMAINS[i]
            if anchor in text_lower:
                weight = 1.0 + text_lower.count(anchor) * 0.5
                vec[i] += weight * 2.5

        # 2. Token n-grams hashing (Dimensions 64 to 383)
        tokens = re.findall(r'\w+', text_lower)
        for t in tokens:
            if len(t) < 2:
                continue
            # Hash token to target dimension in range [64, 383]
            h = int(hashlib.md5(t.encode('utf-8')).hexdigest()[:8], 16)
            dim = 64 + (h % (cls.DIMENSION - 64))
            vec[dim] += 1.0

        # Subword trigrams for morphological similarity
        for i in range(len(text_lower) - 2):
            trigram = text_lower[i:i+3]
            h = int(hashlib.md5(trigram.encode('utf-8')).hexdigest()[:6], 16)
            dim = 64 + (h % (cls.DIMENSION - 64))
            vec[dim] += 0.15

        # Normalize to unit vector for cosine distance
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()


class QdrantVectorService:
    """
    Enterprise-grade vector storage & semantic discovery service powered by Qdrant.
    Supports both remote Qdrant cloud/instances and embedded zero-config local storage.
    """

    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION or "news_articles"
        self.client: Optional[QdrantClient] = None
        self.is_connected = False
        self.mode = "uninitialized"
        self._init_client()

    def _init_client(self):
        """Initialize Qdrant client connection (Remote or Embedded)."""
        if settings.QDRANT_URL:
            try:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=5.0
                )
                self.client.get_collections()
                self.is_connected = True
                self.mode = "remote"
                logger.info(f"Connected to remote Qdrant Vector DB at {settings.QDRANT_URL}")
            except Exception as e:
                logger.warning(f"Remote Qdrant connection failed ({e}). Falling back to embedded local storage.")
                self._init_local_client()
        else:
            self._init_local_client()

        if self.is_connected:
            self._ensure_collection()

    def _init_local_client(self):
        """Initialize local on-disk embedded Qdrant client with in-memory fallback."""
        storage_path = settings.QDRANT_STORAGE_PATH or "./qdrant_storage"
        try:
            os.makedirs(storage_path, exist_ok=True)
            self.client = QdrantClient(path=storage_path)
            self.client.get_collections()
            self.is_connected = True
            self.mode = "embedded_disk"
            logger.info(f"Initialized Embedded Local Qdrant Vector DB at '{storage_path}'")
        except Exception as e:
            logger.warning(f"Failed to open on-disk Qdrant storage ({e}). Falling back to in-memory Qdrant instance.")
            try:
                self.client = QdrantClient(":memory:")
                self.is_connected = True
                self.mode = "in_memory"
                logger.info("Initialized In-Memory Qdrant Vector DB fallback.")
            except Exception as mem_err:
                logger.error(f"In-memory Qdrant initialization failed: {mem_err}")
                self.is_connected = False
                self.mode = "failed"

    def _ensure_collection(self):
        """Ensure news articles vector collection exists with cosine distance index."""
        if not self.is_connected or not self.client:
            return
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=SemanticVectorizer.DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant vector collection '{self.collection_name}' (size={SemanticVectorizer.DIMENSION}, distance=COSINE).")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def embed_text(self, text: str) -> List[float]:
        """Generates dense vector for query or article text."""
        return SemanticVectorizer.embed_text(text)

    def upsert_article(self, article: Any) -> Optional[str]:
        """
        Generates vector embedding and indexes an article into Qdrant.
        Accepts ArticleModel, ArticleRead, or dict.
        """
        if not self.is_connected or not self.client:
            return None

        try:
            # Extract attributes
            art_id = getattr(article, "id", None) or (article.get("id") if isinstance(article, dict) else str(uuid.uuid4()))
            title = getattr(article, "title", None) or (article.get("title", "") if isinstance(article, dict) else "")
            description = getattr(article, "description", "") or (article.get("description", "") if isinstance(article, dict) else "")
            content = getattr(article, "content", "") or (article.get("content", "") if isinstance(article, dict) else "")
            source = getattr(article, "source", "") or (article.get("source", "") if isinstance(article, dict) else "")
            url = getattr(article, "url", "") or (article.get("url", "") if isinstance(article, dict) else "")
            target_entity = getattr(article, "target_entity", "") or (article.get("target_entity", "All Companies") if isinstance(article, dict) else "All Companies")
            relevance_score = getattr(article, "relevance_score", 0.0) or (article.get("relevance_score", 0.0) if isinstance(article, dict) else 0.0)
            importance_rating = getattr(article, "importance_rating", "MEDIUM") or (article.get("importance_rating", "MEDIUM") if isinstance(article, dict) else "MEDIUM")
            sentiment_tone = getattr(article, "sentiment_tone", "Neutral") or (article.get("sentiment_tone", "Neutral") if isinstance(article, dict) else "Neutral")
            ai_summary = getattr(article, "ai_summary", "") or (article.get("ai_summary", "") if isinstance(article, dict) else "")
            reasoning_trace = getattr(article, "reasoning_trace", "") or (article.get("reasoning_trace", "") if isinstance(article, dict) else "")
            published_at = getattr(article, "published_at", None) or (article.get("published_at") if isinstance(article, dict) else None)

            pub_str = published_at.isoformat() if isinstance(published_at, datetime) else str(published_at or "")

            combined_text = f"{title}. {description or ''} {content or ''}"
            vector = self.embed_text(combined_text)

            # Generate valid deterministic UUID for Qdrant point
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"article:{art_id}"))

            payload = {
                "article_id": art_id,
                "title": title,
                "description": description,
                "source": source,
                "url": url,
                "target_entity": target_entity,
                "relevance_score": float(relevance_score or 0.0),
                "importance_rating": importance_rating,
                "sentiment_tone": sentiment_tone,
                "ai_summary": ai_summary,
                "reasoning_trace": reasoning_trace,
                "published_at": pub_str,
                "indexed_at": datetime.utcnow().isoformat()
            }

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            return point_id
        except Exception as e:
            logger.warning(f"Failed to index article into Qdrant: {e}")
            return None

    def bulk_upsert(self, articles: List[Any]) -> int:
        """Bulk indexes a batch of articles into Qdrant."""
        if not self.is_connected or not self.client or not articles:
            return 0

        indexed_count = 0
        points = []
        for article in articles:
            try:
                art_id = getattr(article, "id", None) or (article.get("id") if isinstance(article, dict) else str(uuid.uuid4()))
                title = getattr(article, "title", None) or (article.get("title", "") if isinstance(article, dict) else "")
                desc = getattr(article, "description", "") or (article.get("description", "") if isinstance(article, dict) else "")
                combined_text = f"{title}. {desc or ''}"
                vector = self.embed_text(combined_text)
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"article:{art_id}"))

                pub = getattr(article, "published_at", None) or (article.get("published_at") if isinstance(article, dict) else None)
                pub_str = pub.isoformat() if isinstance(pub, datetime) else str(pub or "")

                payload = {
                    "article_id": art_id,
                    "title": title,
                    "description": desc,
                    "source": getattr(article, "source", "") or (article.get("source", "") if isinstance(article, dict) else ""),
                    "url": getattr(article, "url", "") or (article.get("url", "") if isinstance(article, dict) else ""),
                    "target_entity": getattr(article, "target_entity", "All Companies") or "All Companies",
                    "relevance_score": float(getattr(article, "relevance_score", 0.0) or 0.0),
                    "importance_rating": getattr(article, "importance_rating", "MEDIUM") or "MEDIUM",
                    "sentiment_tone": getattr(article, "sentiment_tone", "Neutral") or "Neutral",
                    "ai_summary": getattr(article, "ai_summary", "") or "",
                    "reasoning_trace": getattr(article, "reasoning_trace", "") or "",
                    "published_at": pub_str,
                    "indexed_at": datetime.utcnow().isoformat()
                }

                points.append(PointStruct(id=point_id, vector=vector, payload=payload))
            except Exception as parse_err:
                logger.debug(f"Error parsing article for Qdrant batch: {parse_err}")

        if points:
            try:
                self.client.upsert(collection_name=self.collection_name, points=points)
                indexed_count = len(points)
                logger.info(f"Successfully bulk-indexed {indexed_count} articles into Qdrant collection '{self.collection_name}'.")
            except Exception as batch_err:
                logger.error(f"Failed Qdrant bulk upsert: {batch_err}")

        return indexed_count

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.4,
        entity_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches Qdrant for articles semantically related to the query vector.
        Returns matched article payloads with cosine similarity scores.
        """
        if not self.is_connected or not self.client:
            return []

        try:
            query_vector = self.embed_text(query)

            # Build Qdrant filter if entity specified
            query_filter = None
            if entity_filter and entity_filter.strip().lower() not in ["all", "all companies"]:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="target_entity",
                            match=MatchValue(value=entity_filter.strip())
                        )
                    ]
                )

            # Query Qdrant
            search_results = []
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=min_score
                )
                search_results = response.points
            else:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=min_score
                )

            results = []
            for hit in search_results:
                payload = hit.payload or {}
                score = float(hit.score)
                results.append({
                    "id": payload.get("article_id") or str(hit.id),
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "source": payload.get("source", ""),
                    "url": payload.get("url", ""),
                    "target_entity": payload.get("target_entity", "All Companies"),
                    "relevance_score": payload.get("relevance_score", 0.0),
                    "importance_rating": payload.get("importance_rating", "MEDIUM"),
                    "sentiment_tone": payload.get("sentiment_tone", "Neutral"),
                    "ai_summary": payload.get("ai_summary", ""),
                    "reasoning_trace": payload.get("reasoning_trace", ""),
                    "published_at": payload.get("published_at"),
                    "similarity_score": round(score, 4),
                    "score_percentage": min(100, int(score * 100))
                })

            return results
        except Exception as e:
            logger.error(f"Qdrant semantic search error: {e}")
            return []

    def find_similar_articles(self, article_id: str, limit: int = 5, min_score: float = 0.45) -> List[Dict[str, Any]]:
        """Finds nearest neighbor articles in Qdrant vector space for a given article."""
        if not self.is_connected or not self.client:
            return []

        try:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"article:{article_id}"))
            points = self.client.retrieve(collection_name=self.collection_name, ids=[point_id], with_vectors=True)
            if not points or not points[0].vector:
                return []

            target_vector = points[0].vector

            search_results = []
            if hasattr(self.client, "query_points"):
                resp = self.client.query_points(
                    collection_name=self.collection_name,
                    query=target_vector,
                    limit=limit + 1,
                    score_threshold=min_score
                )
                search_results = resp.points
            else:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=target_vector,
                    limit=limit + 1,
                    score_threshold=min_score
                )

            similar = []
            for hit in search_results:
                hit_art_id = hit.payload.get("article_id") if hit.payload else None
                if hit_art_id == article_id or str(hit.id) == point_id:
                    continue  # Skip self

                payload = hit.payload or {}
                score = float(hit.score)
                similar.append({
                    "id": payload.get("article_id") or str(hit.id),
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "source": payload.get("source", ""),
                    "url": payload.get("url", ""),
                    "target_entity": payload.get("target_entity", "All Companies"),
                    "relevance_score": payload.get("relevance_score", 0.0),
                    "importance_rating": payload.get("importance_rating", "MEDIUM"),
                    "sentiment_tone": payload.get("sentiment_tone", "Neutral"),
                    "ai_summary": payload.get("ai_summary", ""),
                    "reasoning_trace": payload.get("reasoning_trace", ""),
                    "published_at": payload.get("published_at"),
                    "similarity_score": round(score, 4),
                    "score_percentage": min(100, int(score * 100))
                })

            return similar[:limit]
        except Exception as e:
            logger.error(f"Error finding similar articles in Qdrant: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        """Returns Qdrant vector database health and telemetry status."""
        points_count = 0
        if self.is_connected and self.client:
            try:
                coll_info = self.client.get_collection(self.collection_name)
                points_count = coll_info.points_count or getattr(coll_info, "vectors_count", 0) or 0
            except Exception:
                points_count = 0

        return {
            "status": "connected" if self.is_connected else "disconnected",
            "mode": self.mode,
            "collection": self.collection_name,
            "dimension": SemanticVectorizer.DIMENSION,
            "distance": "Cosine",
            "indexed_vectors": points_count
        }


# Global singleton instance
qdrant_service_instance = QdrantVectorService()
