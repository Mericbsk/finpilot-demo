"""Runtime contract tests for the FastAPI surface."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from auth.database import Database, UserRepository
from auth.users import UserRole


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_DB_PATH", str(tmp_path / "finpilot-test.db"))
    monkeypatch.setenv(
        "FINPILOT_SECRET_KEY",
        "test-secret-key-not-for-production-1234567890",
    )

    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_runtime_health_contract(client: TestClient):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] in {"healthy", "degraded"}

    metrics = client.get("/api/v1/metrics")
    assert metrics.status_code == 200
    assert "FinPilot Metrics Export" in metrics.text


def test_trade_surface_requires_auth(client: TestClient):
    response = client.get("/api/v1/trade/account")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid authentication token"


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/scan", {"symbols": ["AAPL"]}),
        (
            "/api/v1/backtest",
            {
                "symbol": "AAPL",
                "strategy": "Momentum",
                "period": "1y",
                "initial_capital": 10000,
                "position_size_pct": 25,
                "stop_loss_pct": 5,
                "take_profit_pct": 15,
            },
        ),
        ("/api/v1/inference/run", {"symbols": ["AAPL"], "model_version": "active"}),
        ("/api/v1/ensemble", {"symbols": ["AAPL"], "max_symbols": 1}),
        ("/api/v1/llm/analyze", {"symbol": "AAPL", "language": "en", "context": "quick test"}),
    ],
)
def test_compute_surface_requires_auth(client: TestClient, path: str, payload: dict[str, object]):
    response = client.post(path, json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid authentication token"


def test_admin_mutations_require_auth(client: TestClient):
    activate_model = client.post("/api/v1/models/non-existent/activate")
    assert activate_model.status_code == 401

    activate_best = client.post("/api/v1/models/activate-best")
    assert activate_best.status_code == 401

    optuna_run = client.post("/api/v1/optuna/run", json={"agent": "conservative", "n_trials": 1})
    assert optuna_run.status_code == 401


def _promote_user_to_admin(email: str):
    db = Database(os.environ["FINPILOT_DB_PATH"])
    db.initialize()
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    assert user is not None
    user.role = UserRole.ADMIN
    user.is_verified = True
    repo.save(user)


def test_auth_register_login_and_me_flow(client: TestClient):
    payload = {
        "email": "alice@example.com",
        "username": "alice",
        "password": "SecurePass123!",  # pragma: allowlist secret
        "display_name": "Alice",
    }

    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201
    body = register.json()
    assert body["user"]["email"] == payload["email"]
    assert body["access_token"]
    assert body["refresh_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == payload["username"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": body["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    forbidden_activate = client.post(
        "/api/v1/models/non-existent/activate",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert forbidden_activate.status_code == 403

    forbidden_optuna = client.post(
        "/api/v1/optuna/run",
        json={"agent": "conservative", "n_trials": 1},
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert forbidden_optuna.status_code == 403

    _promote_user_to_admin(payload["email"])
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"], "remember_me": True},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    authorized_activate = client.post(
        "/api/v1/models/non-existent/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert authorized_activate.status_code == 404

    authorized_optuna = client.post(
        "/api/v1/optuna/run",
        json={"agent": "conservative", "n_trials": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert authorized_optuna.status_code == 200
    assert authorized_optuna.json()["status"] == "running"


def test_anonymous_settings_are_limited_to_demo_profile(client: TestClient):
    forbidden = client.put(
        "/api/v1/user/settings",
        json={"user_id": "someone-else", "settings": {"market": "US"}},
    )
    assert forbidden.status_code == 403

    allowed = client.put(
        "/api/v1/user/settings",
        json={"user_id": "default", "settings": {"market": "US"}},
    )
    assert allowed.status_code == 200
    assert allowed.json()["user_id"] == "default"
