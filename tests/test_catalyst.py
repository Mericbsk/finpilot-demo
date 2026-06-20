"""Tests for the SEC EDGAR catalyst feed (env-gated, default OFF)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
import scanner.catalyst as cat
import scanner.score_engine as se


@pytest.fixture(autouse=True)
def _reset_caches(monkeypatch):
    cat._TICKER_CIK_MAP = None
    cat._FACTOR_CACHE = None
    monkeypatch.setenv("FINPILOT_ENABLE_EDGAR_CATALYST", "1")
    yield
    cat._TICKER_CIK_MAP = None
    cat._FACTOR_CACHE = None


def _recent(*forms_dates):
    return {
        "filings": {
            "recent": {
                "form": [f for f, _ in forms_dates],
                "filingDate": [d for _, d in forms_dates],
            }
        }
    }


def test_score_filings_8k_positive():
    assert cat._score_filings([{"form": "8-K", "date": "2026-06-18"}]) == pytest.approx(0.6)


def test_score_filings_offering_negative():
    assert cat._score_filings([{"form": "424B5", "date": "2026-06-18"}]) == pytest.approx(-0.5)


def test_score_filings_dedupes_same_form():
    filings = [{"form": "8-K", "date": "2026-06-18"}, {"form": "8-K", "date": "2026-06-17"}]
    assert cat._score_filings(filings) == pytest.approx(0.6)  # counted once


def test_score_filings_mixed_clamped():
    filings = [
        {"form": "8-K", "date": "2026-06-18"},
        {"form": "4", "date": "2026-06-18"},
        {"form": "S-1", "date": "2026-06-18"},
    ]
    # 0.6 + 0.3 - 0.5 = 0.4
    assert cat._score_filings(filings) == pytest.approx(0.4)


def test_score_filings_unknown_form_ignored():
    assert cat._score_filings([{"form": "10-Q", "date": "2026-06-18"}]) == 0.0


def test_fetch_recent_filings_filters_by_date(monkeypatch):
    today = datetime.now(tz=UTC).date()
    old = (today - timedelta(days=30)).isoformat()
    fresh = (today - timedelta(days=1)).isoformat()

    monkeypatch.setattr(cat, "_load_ticker_cik_map", lambda force=False: {"XYZ": "123"})
    monkeypatch.setattr(cat, "_get", lambda url: _recent(("8-K", fresh), ("10-K", old)))
    out = cat.fetch_recent_filings("XYZ", days=7)
    assert out == [{"form": "8-K", "date": fresh}]


def test_compute_catalyst_factor_disabled_is_zero(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_EDGAR_CATALYST", "0")
    cat._FACTOR_CACHE = {"XYZ": 0.6}
    assert cat.compute_catalyst_factor("XYZ") == 0.0


def test_compute_catalyst_factor_reads_cache():
    cat._FACTOR_CACHE = {"XYZ": 0.6}
    assert cat.compute_catalyst_factor("xyz") == pytest.approx(0.6)
    assert cat.compute_catalyst_factor("UNKNOWN") == 0.0


def test_refresh_catalyst_cache_writes_file(monkeypatch, tmp_path):
    monkeypatch.setattr(cat, "_CACHE_PATH", tmp_path / "catalyst_cache.json")
    monkeypatch.setattr(cat, "_RATE_LIMIT_SLEEP", 0.0)
    monkeypatch.setattr(cat, "_load_ticker_cik_map", lambda force=False: {"XYZ": "1"})
    today = datetime.now(tz=UTC).date().isoformat()
    monkeypatch.setattr(cat, "_get", lambda url: _recent(("8-K", today)))

    factors = cat.refresh_catalyst_cache(["XYZ"])
    assert factors["XYZ"] == pytest.approx(0.6)
    payload = json.loads((tmp_path / "catalyst_cache.json").read_text(encoding="utf-8"))
    assert payload["factors"]["XYZ"] == pytest.approx(0.6)


def test_score_engine_catalyst_off_by_default(monkeypatch):
    monkeypatch.delenv("FINPILOT_ENABLE_EDGAR_CATALYST", raising=False)
    assert se.compute_recommendation_score({"score": 3, "catalyst_factor": 1.0}) == 3.0


def test_score_engine_catalyst_signed_when_enabled(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_EDGAR_CATALYST", "1")
    base = se.compute_recommendation_score({"score": 3, "catalyst_factor": 0.0})
    pos = se.compute_recommendation_score({"score": 3, "catalyst_factor": 1.0})
    neg = se.compute_recommendation_score({"score": 3, "catalyst_factor": -1.0})
    assert pos - base == pytest.approx(se._CATALYST_WEIGHT)
    assert base - neg == pytest.approx(se._CATALYST_WEIGHT)
