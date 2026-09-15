from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class SourceRoutingDecision(BaseModel):
    source_id: str
    source_name: str
    selected: bool
    connection_method: str
    reason: str
    priority: int
    estimated_cost: float
    availability: str
    skip_reason: Optional[str] = None

class OverallRoutingDecision(BaseModel):
    request_id: str
    entity: str
    timestamp: str
    selected_sources: List[SourceRoutingDecision]
    skipped_sources: List[SourceRoutingDecision]
    cache_decision: str  # HIT, MISS, BYPASS
    total_estimated_cost: float
