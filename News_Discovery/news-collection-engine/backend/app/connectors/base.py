from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.article import ArticleCreate

class BaseConnector(ABC):
    """Abstract base class for all news collection connectors."""

    def __init__(self, source_config: Dict[str, Any]):
        self.source_config = source_config
        self.source_id = source_config.get("id")
        self.source_name = source_config.get("name")
        self.connection_method = source_config.get("connection_method", "api")

    @abstractmethod
    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        """Validate if API key or RSS URL is configured properly."""
        pass

    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """Check if source is enabled, key configured, and within rate limits."""
        pass

    @abstractmethod
    def build_query(self, entity: str, keywords: List[str], location: Optional[str] = None, category: Optional[str] = None) -> str:
        """Construct source-specific query string."""
        pass

    @abstractmethod
    async def fetch(self, query: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Fetch raw articles from external API or RSS feed."""
        pass

    @abstractmethod
    def normalize(self, raw_items: List[Dict[str, Any]]) -> List[ArticleCreate]:
        """Normalize raw source items into unified ArticleCreate schemas."""
        pass

    @abstractmethod
    def get_rate_status(self) -> Dict[str, Any]:
        """Return rate limit window usage metrics."""
        pass
