import json
import hashlib
import time
from typing import Optional, Dict, Any, Tuple, List
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("news_engine.cache_service")

class InMemoryCacheFallback:
    """In-memory dictionary cache fallback with TTL management."""
    def __init__(self):
        self._store: Dict[str, Tuple[str, float]] = {}

    def get(self, key: str) -> Optional[str]:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def setex(self, key: str, ttl_seconds: int, value: str):
        expires_at = time.time() + ttl_seconds
        self._store[key] = (value, expires_at)

    def size(self) -> int:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(self._store)

class CacheService:
    """Redis cache service with seamless in-memory fallback."""

    def __init__(self):
        self.ttl_seconds = settings.CACHE_TTL_SECONDS
        self.redis_client = None
        self.in_memory_fallback = InMemoryCacheFallback()
        self.is_redis_active = False

        if settings.REDIS_URL:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2.0)
                self.redis_client.ping()
                self.is_redis_active = True
                logger.info(f"Connected to Redis cache at {settings.REDIS_URL}")
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}). Activated in-memory cache fallback.")
                self.is_redis_active = False
        else:
            logger.info("REDIS_URL not configured. Operating in-memory cache fallback.")

    @staticmethod
    def generate_cache_key(
        entity: str,
        keywords: List[str],
        location: Optional[str] = None,
        category: Optional[str] = None,
        time_window_minutes: int = 60,
        min_relevance: Optional[float] = None
    ) -> str:
        norm_entity = entity.strip().lower()
        norm_kw = ",".join(sorted([k.strip().lower() for k in keywords if k.strip()]))
        kw_hash = hashlib.md5(norm_kw.encode('utf-8')).hexdigest()[:8]
        norm_loc = (location or "all").strip().lower()
        norm_cat = (category or "all").strip().lower()
        rel_str = f":rel{int(min_relevance)}" if min_relevance is not None else ""
        return f"news:{norm_entity}:{kw_hash}:{norm_loc}:{norm_cat}:{time_window_minutes}{rel_str}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached JSON payload if key exists and is unexpired."""
        raw_val = None
        if self.is_redis_active and self.redis_client:
            try:
                raw_val = self.redis_client.get(key)
            except Exception as e:
                logger.warning(f"Redis get error: {e}. Checking fallback.")
                raw_val = self.in_memory_fallback.get(key)
        else:
            raw_val = self.in_memory_fallback.get(key)

        if raw_val:
            try:
                logger.info(f"Cache HIT for key: {key}")
                return json.loads(raw_val)
            except Exception as e:
                logger.error(f"Failed to deserialize cache payload for {key}: {e}")
                return None
        
        logger.info(f"Cache MISS for key: {key}")
        return None

    def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """Store JSON payload in cache with TTL."""
        ttl_val = ttl or self.ttl_seconds
        serialized = json.dumps(data, default=str)

        if self.is_redis_active and self.redis_client:
            try:
                self.redis_client.setex(key, ttl_val, serialized)
            except Exception as e:
                logger.warning(f"Redis setex error: {e}. Storing in memory fallback.")
                self.in_memory_fallback.setex(key, ttl_val, serialized)
        else:
            self.in_memory_fallback.setex(key, ttl_val, serialized)

    def get_status(self) -> Dict[str, Any]:
        """Return cache health & status diagnostics."""
        return {
            "redis_connected": self.is_redis_active,
            "fallback_mode": not self.is_redis_active,
            "in_memory_keys_count": self.in_memory_fallback.size(),
            "default_ttl_seconds": self.ttl_seconds
        }

cache_service_instance = CacheService()
