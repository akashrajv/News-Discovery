import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import SourceModel
from app.registry.source_registry import SourceRegistry
from app.schemas.routing import SourceRoutingDecision, OverallRoutingDecision
from app.utils.logger import get_logger

logger = get_logger("news_engine.source_router")

class SourceRouter:
    """Cost-aware router evaluating source priority, availability, API keys, quota, and RSS preference."""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_routing(
        self,
        request_id: str,
        entity: str,
        cache_hit: bool = False,
        demo_mode: bool = False
    ) -> OverallRoutingDecision:
        sources = SourceRegistry.get_all_sources(self.db)
        
        selected_decisions: List[SourceRoutingDecision] = []
        skipped_decisions: List[SourceRoutingDecision] = []
        total_cost = 0.0

        if cache_hit:
            # Cache hit decision summary
            for s in sources:
                skipped_decisions.append(
                    SourceRoutingDecision(
                        source_id=s.id,
                        source_name=s.name,
                        selected=False,
                        connection_method=s.connection_method,
                        reason="Skipped: Equivalent query found in cache (0 additional request cost)",
                        priority=s.priority,
                        estimated_cost=s.estimated_cost_per_request,
                        availability=s.current_status,
                        skip_reason="cached_equivalent_exists"
                    )
                )
            return OverallRoutingDecision(
                request_id=request_id,
                entity=entity,
                timestamp=datetime.utcnow().isoformat(),
                selected_sources=[],
                skipped_sources=skipped_decisions,
                cache_decision="HIT",
                total_estimated_cost=0.0
            )

        # Sort sources by priority descending, then by estimated cost ascending
        sorted_sources = sorted(sources, key=lambda s: (-s.priority, s.estimated_cost_per_request))

        for source in sorted_sources:
            connector = SourceRegistry.get_connector(source)
            avail, avail_reason = connector.is_available()

            if demo_mode:
                # In demo mode, select all enabled sources to demonstrate multi-source collection
                if source.enabled:
                    selected_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=True,
                            connection_method=source.connection_method,
                            reason="Selected (Demo Mode active: deterministic mock collection enabled)",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="AVAILABLE"
                        )
                    )
                    total_cost += source.estimated_cost_per_request
                else:
                    skipped_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=False,
                            connection_method=source.connection_method,
                            reason="Skipped: Source explicitly disabled in registry",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="DISABLED",
                            skip_reason="disabled"
                        )
                    )
                continue

            # Live evaluation logic
            if not source.enabled:
                skipped_decisions.append(
                    SourceRoutingDecision(
                        source_id=source.id,
                        source_name=source.name,
                        selected=False,
                        connection_method=source.connection_method,
                        reason="Skipped: Source explicitly disabled",
                        priority=source.priority,
                        estimated_cost=source.estimated_cost_per_request,
                        availability="DISABLED",
                        skip_reason="disabled"
                    )
                )
                continue

            if source.connection_method == "rss":
                if avail:
                    selected_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=True,
                            connection_method="rss",
                            reason="Selected: Public RSS available, high priority, zero API request cost",
                            priority=source.priority,
                            estimated_cost=0.0,
                            availability="AVAILABLE"
                        )
                    )
                else:
                    skipped_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=False,
                            connection_method="rss",
                            reason=f"Skipped RSS: {avail_reason}",
                            priority=source.priority,
                            estimated_cost=0.0,
                            availability="UNAVAILABLE",
                            skip_reason=avail_reason
                        )
                    )
            elif source.connection_method == "api":
                if not source.api_key_configured and not os.getenv(source.api_key_env_name or ""):
                    skipped_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=False,
                            connection_method="api",
                            reason=f"Skipped API: API key env var '{source.api_key_env_name}' not configured",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="UNAVAILABLE",
                            skip_reason="api_key_missing"
                        )
                    )
                elif source.requests_remaining <= 0:
                    skipped_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=False,
                            connection_method="api",
                            reason="Skipped API: Configured quota limit reached for window",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="RATE_LIMITED",
                            skip_reason="quota_exhausted"
                        )
                    )
                elif not avail:
                    skipped_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=False,
                            connection_method="api",
                            reason=f"Skipped API: {avail_reason}",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="UNAVAILABLE",
                            skip_reason=avail_reason
                        )
                    )
                else:
                    selected_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=True,
                            connection_method="api",
                            reason=f"Selected API: Key configured, quota remaining ({source.requests_remaining}), estimated cost ${source.estimated_cost_per_request}",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="AVAILABLE"
                        )
                    )
                    total_cost += source.estimated_cost_per_request
            elif source.connection_method == "authorized_feed":
                if avail:
                    selected_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=True,
                            connection_method="authorized_feed",
                            reason="Selected: Authorized structured feed available",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="AVAILABLE"
                        )
                    )
                    total_cost += source.estimated_cost_per_request
                else:
                    skipped_decisions.append(
                        SourceRoutingDecision(
                            source_id=source.id,
                            source_name=source.name,
                            selected=False,
                            connection_method="authorized_feed",
                            reason=f"Skipped Feed: {avail_reason}",
                            priority=source.priority,
                            estimated_cost=source.estimated_cost_per_request,
                            availability="UNAVAILABLE",
                            skip_reason=avail_reason
                        )
                    )

        return OverallRoutingDecision(
            request_id=request_id,
            entity=entity,
            timestamp=datetime.utcnow().isoformat(),
            selected_sources=selected_decisions,
            skipped_sources=skipped_decisions,
            cache_decision="MISS",
            total_estimated_cost=total_cost
        )
