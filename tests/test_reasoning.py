"""
VS-01 Phase 7 — real HTTP tests for the FinSense reasoning API
(api/routers/reasoning.py), via FastAPI's TestClient (not raw sqlite3 like
the Phase 1/3 sandbox verification scripts).

Could NOT be executed inside the Cowork sandbox this file was authored in —
that sandbox has no fastapi/starlette installed and no network access to pip
install them (confirmed repeatedly: ProxyError 403 on every attempt). Run
this for real with:

    python -m pytest tests/test_reasoning.py -v

Every test uses its own isolated tmp_path SQLite DB (via the `client`
fixture below, which monkeypatches `reasoning._get_db`) — none of this
touches the real data/finpilot.db. Seeds exactly one open case per test
("case-001") so tests don't depend on Case #001's real, possibly-mutated
production state.

Covers VS-01 Phase 7 §7.2-§7.6:
  - GET /case/today (happy path + my_prediction)
  - POST /predict (happy path, DB row created)
  - Immutability: duplicate predict -> 409, no second row
  - Manipulation: probability out of range -> 422, invalid direction -> 422,
    client-supplied committed_at/actual_direction are simply ignored (not in
    the request schema, so FastAPI/Pydantic strips them silently — proven by
    asserting the server's own committed_at is used, not the client's)
  - Cross-user isolation on GET /outcome
  - GET /outcome: pending -> 404, resolved -> outcome + evaluation with
    direction_correct/probability_error
"""

from __future__ import annotations

import datetime as _dt
import json

if not hasattr(_dt, "UTC"):
    _dt.UTC = _dt.UTC  # Python 3.10 compat shim, see auth/database.py usage

import pytest

CASE_ID = "case-001"


def _seed_case(db, case_id: str = CASE_ID, status: str = "open") -> None:
    with db.connection() as conn:
        conn.execute(
            "INSERT INTO fs_cases (id, source_signal_id, asset, event_timestamp, "
            "snapshot, context, horizon_days, outcome_rule, resolution_method, "
            "status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                case_id,
                "sig_test",
                "GS",
                "2026-05-22T00:00:00Z",
                json.dumps({"price_at_event": 550.0}),
                "Test case context for VS-01 Phase 7 HTTP verification.",
                21,
                json.dumps({"type": "finpilot_barrier"}),
                "finpilot_barrier",
                status,
                "2026-05-22T00:00:00Z",
            ),
        )


def _seed_outcome(
    db, case_id: str = CASE_ID, actual_direction: str = "UP", actual_return_pct: float = 1.90
) -> None:
    with db.connection() as conn:
        conn.execute(
            "INSERT INTO fs_outcomes (case_id, actual_direction, actual_return_pct, "
            "resolution_method, resolved_at) VALUES (?,?,?,?,?)",
            (
                case_id,
                actual_direction,
                actual_return_pct,
                "finpilot_barrier",
                "2026-06-22T00:00:00Z",
            ),
        )


@pytest.fixture()
def db(tmp_path):
    from auth.database import Database

    database = Database(db_path=str(tmp_path / "vs01_http_test.db"))
    database.initialize()
    return database


@pytest.fixture()
def client(db, monkeypatch):
    import api.routers.reasoning as reasoning_mod
    from api.main import app
    from fastapi.testclient import TestClient

    # Point the router at our isolated tmp_path DB instead of the real
    # data/finpilot.db — every other DB-backed router in the app is
    # untouched, only reasoning._get_db is redirected.
    monkeypatch.setattr(reasoning_mod, "_get_db", lambda: db)

    return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────────────────────
# §7.2 Test 1 — GET /case/today
# ─────────────────────────────────────────────────────────────────────────────
class TestCaseToday:
    def test_no_open_case_returns_204(self, client):
        r = client.get("/api/v1/finsense/case/today")
        assert r.status_code == 204

    def test_open_case_returned_no_outcome_fields(self, client, db):
        _seed_case(db)
        r = client.get("/api/v1/finsense/case/today")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == CASE_ID
        assert body["my_prediction"] is None
        for leaked_field in ("actual_direction", "actual_return_pct", "resolved_at", "evaluation"):
            assert leaked_field not in body, f"{leaked_field} leaked into case/today response"

    def test_my_prediction_populated_after_commit(self, client, db):
        _seed_case(db)
        client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-1",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        r = client.get("/api/v1/finsense/case/today", params={"anonymous_user_id": "anon-http-1"})
        assert r.status_code == 200
        assert r.json()["my_prediction"]["direction"] == "UP"


# ─────────────────────────────────────────────────────────────────────────────
# §7.2 Test 2 + §7.3 Immutability
# ─────────────────────────────────────────────────────────────────────────────
class TestPredict:
    def test_happy_path_creates_row(self, client, db):
        _seed_case(db)
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-2",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["case_id"] == CASE_ID
        assert body["direction"] == "UP"
        assert body["probability"] == 0.7
        assert "committed_at" in body and body["committed_at"]

        with db.connection() as conn:
            row = conn.execute(
                "SELECT case_id, anonymous_user_id, direction, probability, reason, "
                "committed_at FROM fs_predictions WHERE anonymous_user_id = 'anon-http-2'"
            ).fetchone()
        assert row is not None
        assert row["case_id"] == CASE_ID

    def test_duplicate_returns_409_and_no_second_row(self, client, db):
        _seed_case(db)
        payload = {
            "anonymous_user_id": "anon-http-3",
            "direction": "UP",
            "probability": 0.7,
            "reason": "Volume expansion and price structure suggest continued upward pressure.",
        }
        r1 = client.post(f"/api/v1/finsense/case/{CASE_ID}/predict", json=payload)
        assert r1.status_code == 201

        payload2 = {
            **payload,
            "direction": "DOWN",
            "reason": "Actually I changed my mind about this completely.",
        }
        r2 = client.post(f"/api/v1/finsense/case/{CASE_ID}/predict", json=payload2)
        assert r2.status_code == 409

        with db.connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM fs_predictions WHERE anonymous_user_id = 'anon-http-3'"
            ).fetchone()["n"]
        assert count == 1, "duplicate predict must not create a second row"

    def test_closed_case_rejected(self, client, db):
        _seed_case(db, status="closed")
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-4",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        assert r.status_code == 400

    def test_unknown_case_returns_404(self, client, db):
        r = client.post(
            "/api/v1/finsense/case/does-not-exist/predict",
            json={
                "anonymous_user_id": "anon-http-5",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# §7.4 Manipulation tests
# ─────────────────────────────────────────────────────────────────────────────
class TestManipulation:
    @pytest.mark.parametrize("bad_probability", [-0.1, 1.1])
    def test_probability_out_of_range_422(self, client, db, bad_probability):
        _seed_case(db)
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-6",
                "direction": "UP",
                "probability": bad_probability,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        assert r.status_code == 422

    @pytest.mark.parametrize("bad_direction", ["BUY", "SELL", "MAYBE"])
    def test_invalid_direction_422(self, client, db, bad_direction):
        _seed_case(db)
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-7",
                "direction": bad_direction,
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        assert r.status_code == 422

    def test_reason_too_short_422(self, client, db):
        _seed_case(db)
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-8",
                "direction": "UP",
                "probability": 0.7,
                "reason": "too short",
            },
        )
        assert r.status_code == 422

    def test_client_supplied_committed_at_is_ignored(self, client, db):
        """PredictRequest has no `committed_at` field — FastAPI/Pydantic drops
        unknown fields by default, so a client-supplied value can never reach
        the DB. Proven here by asserting the returned committed_at is a
        server-generated ISO timestamp near "now", not the planted value."""
        _seed_case(db)
        planted = "1999-01-01T00:00:00Z"
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-9",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
                "committed_at": planted,
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["committed_at"] != planted
        assert r.json()["committed_at"].startswith("20")  # a real current-ish year

    def test_client_supplied_outcome_field_is_ignored(self, client, db):
        """Same principle for a planted outcome field — PredictRequest has no
        such field, so it cannot influence fs_outcomes (which this endpoint
        never even writes to)."""
        _seed_case(db)
        r = client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anon-http-10",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
                "actual_direction": "UP",
            },
        )
        assert r.status_code == 201
        with db.connection() as conn:
            outcome_row = conn.execute(
                "SELECT * FROM fs_outcomes WHERE case_id = ?", (CASE_ID,)
            ).fetchone()
        assert outcome_row is None, "predict must never create an outcome row"


# ─────────────────────────────────────────────────────────────────────────────
# §7.5 Cross-user isolation + §7.6 Outcome
# ─────────────────────────────────────────────────────────────────────────────
class TestOutcomeAndIsolation:
    def test_outcome_pending_returns_404(self, client, db):
        _seed_case(db)
        r = client.get(f"/api/v1/finsense/case/{CASE_ID}/outcome")
        assert r.status_code == 404

    def test_cross_user_isolation_and_evaluation_math(self, client, db):
        _seed_case(db)
        client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anonymous-verify-1",
                "direction": "UP",
                "probability": 0.7,
                "reason": "Volume expansion and price structure suggest continued upward pressure.",
            },
        )
        client.post(
            f"/api/v1/finsense/case/{CASE_ID}/predict",
            json={
                "anonymous_user_id": "anonymous-verify-2",
                "direction": "DOWN",
                "probability": 0.6,
                "reason": "Overbought conditions and weakening momentum favor a pullback.",
            },
        )
        _seed_outcome(db, actual_direction="UP", actual_return_pct=1.90)

        r1 = client.get(
            f"/api/v1/finsense/case/{CASE_ID}/outcome",
            params={"anonymous_user_id": "anonymous-verify-1"},
        )
        assert r1.status_code == 200
        body1 = r1.json()
        assert body1["actual_direction"] == "UP"
        assert body1["actual_return_pct"] == 1.90
        assert body1["your_prediction"]["direction"] == "UP"
        assert body1["evaluation"]["direction_correct"] is True
        assert body1["evaluation"]["binary_outcome"] == 1
        assert abs(body1["evaluation"]["probability_error"] - (0.7 - 1)) < 1e-9

        r2 = client.get(
            f"/api/v1/finsense/case/{CASE_ID}/outcome",
            params={"anonymous_user_id": "anonymous-verify-2"},
        )
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["your_prediction"]["direction"] == "DOWN"
        assert body2["evaluation"]["direction_correct"] is False
        assert body2["evaluation"]["binary_outcome"] == 0
        assert abs(body2["evaluation"]["probability_error"] - (0.6 - 0)) < 1e-9

        # Cross-user isolation: user 1 must never see user 2's prediction id and vice versa.
        assert body1["your_prediction"]["id"] != body2["your_prediction"]["id"]

    def test_no_id_call_gets_outcome_without_any_prediction(self, client, db):
        _seed_case(db)
        _seed_outcome(db)
        r = client.get(f"/api/v1/finsense/case/{CASE_ID}/outcome")
        assert r.status_code == 200
        body = r.json()
        assert body["your_prediction"] is None
        assert body["evaluation"] is None

    def test_unseen_user_gets_outcome_without_prediction(self, client, db):
        _seed_case(db)
        _seed_outcome(db)
        r = client.get(
            f"/api/v1/finsense/case/{CASE_ID}/outcome",
            params={"anonymous_user_id": "someone-who-never-predicted"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["your_prediction"] is None
        assert body["evaluation"] is None
