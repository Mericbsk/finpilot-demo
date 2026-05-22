"""HTTP-level tests for GET /api/v1/analytics/summary.

Uses FastAPI TestClient with the full app so the router registration and
middleware are exercised.  Redis is not required — core.analytics falls back
to in-memory counters automatically.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_DB_PATH", str(tmp_path / "finpilot-test.db"))
    monkeypatch.setenv(
        "FINPILOT_SECRET_KEY",
        "test-secret-key-not-for-production-1234567890",
    )

    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Schema contract
# ---------------------------------------------------------------------------


def test_summary_returns_200(client: TestClient):
    resp = client.get("/api/v1/analytics/summary")
    assert resp.status_code == 200


def test_summary_has_required_keys(client: TestClient):
    data = client.get("/api/v1/analytics/summary").json()
    assert "page_views" in data
    assert "events" in data
    assert "collected_at" in data


def test_summary_page_views_is_dict(client: TestClient):
    data = client.get("/api/v1/analytics/summary").json()
    assert isinstance(data["page_views"], dict)


def test_summary_events_is_dict(client: TestClient):
    data = client.get("/api/v1/analytics/summary").json()
    assert isinstance(data["events"], dict)


def test_summary_collected_at_is_iso_string(client: TestClient):
    from datetime import datetime

    data = client.get("/api/v1/analytics/summary").json()
    # Should parse without raising
    dt = datetime.fromisoformat(data["collected_at"])
    assert dt is not None


# ---------------------------------------------------------------------------
# Counter propagation
# ---------------------------------------------------------------------------


def test_event_counter_increments_in_summary(client: TestClient, monkeypatch):
    """Firing an event via core.analytics must appear in the summary response."""
    import core.analytics as analytics

    analytics.increment_event("test_event_abc")

    data = client.get("/api/v1/analytics/summary").json()
    assert data["events"].get("test_event_abc", 0) >= 1


def test_multiple_events_tracked(client: TestClient, monkeypatch):
    import core.analytics as analytics

    analytics.increment_event("ev_x")
    analytics.increment_event("ev_x")
    analytics.increment_event("ev_y")

    data = client.get("/api/v1/analytics/summary").json()
    assert data["events"].get("ev_x", 0) >= 2
    assert data["events"].get("ev_y", 0) >= 1
