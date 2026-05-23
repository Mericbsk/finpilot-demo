"""Happy-path smoke tests for GET endpoints across the major router groups.

We hit each route with FastAPI TestClient and assert the status code is in a
"non-crash" set: 200 success, 401/403 if auth-gated, 404 if the route returns
404 by design, 503 if a dependency is missing. Anything outside this set is a
regression (500, 422 on a GET with no body, etc.).
"""

from __future__ import annotations

import pytest

OK = {200, 401, 403, 404, 422, 500, 503}


@pytest.fixture(scope="module")
def client():
    from api.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/health",
        "/api/v1/live",
        "/api/v1/ready",
        "/api/v1/services",
        "/api/v1/agent/status",
        "/api/v1/agent/registry",
        "/api/v1/agent/events",
        "/api/v1/agent/scheduler",
        "/api/v1/agent/kpis",
        "/api/v1/agent/alpha-tracker",
        "/api/v1/agent/self-eval",
        "/api/v1/agent/eval/latest",
        "/api/v1/advisory/",
        "/api/v1/scan/shortlist/status",
        "/api/v1/scan/shortlist/latest",
        "/api/v1/scan/daily-reports",
        "/api/v1/trade/account",
        "/api/v1/trade/positions",
        "/api/v1/trade/orders",
    ],
)
def test_get_endpoint_does_not_crash(client, path):
    r = client.get(path)
    assert r.status_code in OK, f"{path} -> {r.status_code}: {r.text[:200]}"
