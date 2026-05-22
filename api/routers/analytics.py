"""Analytics router — GET /api/v1/analytics/summary.

Returns lightweight event counters (page views, champion edge queries, scan runs)
collected by ``core.analytics`` without any third-party analytics SDK.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary() -> dict[str, Any]:
    """Return aggregated usage counters.

    Response::

        {
            "page_views": {"/dashboard": 42, "/agent": 10, ...},
            "events":     {"champion_edge_query": 5, "scan_run": 3, ...},
            "collected_at": "2024-01-01T00:00:00+00:00"
        }
    """
    from core.analytics import get_summary

    data = get_summary()
    data["collected_at"] = datetime.now(tz=UTC).isoformat()
    return data
