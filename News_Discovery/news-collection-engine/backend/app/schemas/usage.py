from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel

class UsageSummaryRead(BaseModel):
    api_requests: int
    rss_collections: int
    cache_hits: int
    cache_misses: int
    duplicate_count: int
    successful_requests: int
    failed_requests: int
    estimated_api_cost: float
    cache_hit_rate: float
    source_utilization: Dict[str, Any]
