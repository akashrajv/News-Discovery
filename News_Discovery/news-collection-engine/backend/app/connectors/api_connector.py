import os
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.connectors.base import BaseConnector
from app.utils.logger import get_logger

logger = get_logger("news_engine.api_connector")

class BaseAPIConnector(BaseConnector):
    """Base class for HTTP REST API connectors with environment variable API key checks."""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.api_endpoint = source_config.get("api_endpoint")
        self.api_key_env_name = source_config.get("api_key_env_name")
        self.api_key = os.getenv(self.api_key_env_name, "") if self.api_key_env_name else ""

    def validate_configuration(self) -> Tuple[bool, Optional[str]]:
        if not self.api_key_env_name:
            return False, "API key environment variable name not specified"
        if not self.api_key:
            return False, f"API key not configured in environment variable '{self.api_key_env_name}'"
        if not self.api_endpoint:
            return False, "API endpoint URL not specified"
        return True, None

    def is_available(self) -> Tuple[bool, str]:
        if not self.source_config.get("enabled", True):
            return False, "Source is disabled"
        
        valid, msg = self.validate_configuration()
        if not valid:
            return False, msg or "API key missing"

        req_used = self.source_config.get("requests_used", 0)
        req_limit = self.source_config.get("request_limit", 100)
        if req_used >= req_limit:
            return False, f"API quota exhausted ({req_used}/{req_limit})"

        return True, "Available (Configured & Authorized)"

    def get_rate_status(self) -> Dict[str, Any]:
        req_used = self.source_config.get("requests_used", 0)
        req_limit = self.source_config.get("request_limit", 100)
        return {
            "requests_used": req_used,
            "requests_remaining": max(0, req_limit - req_used),
            "window_seconds": self.source_config.get("rate_limit_window_seconds", 86400)
        }
