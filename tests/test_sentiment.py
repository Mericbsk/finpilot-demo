"""Tests for scanner.sentiment — EODHD News Sentiment factor (cache-based).

All pure / deterministic — NO network. The scan hot path only reads the cache,
so these cover: normalisation (-1..1 → 0..1), EODHD response parsing, cache
read + neutral default, and the enable-gate logic. The network refresh path is
exercised with a monkeypatched _get so no real EODHD call is made.
"""

from __future__ import annotations

import json

from scanner import sentiment as S


# ── normalisation ────────────────────────────────────────────────────────────
def test_normalise_maps_neutral_to_half():
    assert S._normalise(0.0) == 0.5


def test_normalise_maps_extremes():
    assert S._normalise(1.0) == 1.0
    assert S._normalise(-1.0) == 0.0


def test_normalise_clamps_and_handles_bad():
    assert S._normalise(5.0) == 1.0
    assert S._normalise(-5.0) == 0.0
    assert S._normalise("x") == 0.5  # bad input → neutral


# ── EODHD response parsing ───────────────────────────────────────────────────
def test_latest_normalised_dict_shape():
    payload = {
        "AAPL.US": [
            {"date": "2026-06-10", "count": 3, "normalized": -0.2},
            {"date": "2026-06-11", "count": 5, "normalized": 0.4},
        ]
    }
    assert S._latest_normalised_for(payload, "AAPL.US") == 0.4  # most recent


def test_latest_normalised_single_key_fallback():
    payload = {"WHATEVER": [{"date": "d", "normalized": 0.9}]}
    assert S._latest_normalised_for(payload, "AAPL.US") == 0.9  # single-key fallback


def test_latest_normalised_missing_returns_none():
    assert S._latest_normalised_for({}, "AAPL.US") is None
    assert S._latest_normalised_for({"AAPL.US": []}, "AAPL.US") is None


# ── cache read (hot path) ────────────────────────────────────────────────────
def test_compute_sentiment_factor_from_cache(tmp_path, monkeypatch):
    cache = tmp_path / "sentiment_cache.json"
    cache.write_text(json.dumps({"NVDA": 0.8}), encoding="utf-8")
    monkeypatch.setattr(S, "_CACHE_PATH", cache)
    assert S.compute_sentiment_factor("NVDA") == 0.8


def test_compute_sentiment_factor_missing_is_neutral(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "_CACHE_PATH", tmp_path / "does_not_exist.json")
    assert S.compute_sentiment_factor("NVDA") == 0.5  # neutral → no score effect


# ── enable gate ──────────────────────────────────────────────────────────────
def test_sentiment_enabled_requires_flag_and_key(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SENTIMENT", "1")
    monkeypatch.delenv("EODHD_API_KEY", raising=False)
    assert S.sentiment_enabled() is False  # flag on but no key
    monkeypatch.setenv("EODHD_API_KEY", "abc")
    assert S.sentiment_enabled() is True
    monkeypatch.setenv("FINPILOT_ENABLE_SENTIMENT", "0")
    assert S.sentiment_enabled() is False  # key but flag off


def test_refresh_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SENTIMENT", "0")
    assert S.refresh_sentiment_cache(["AAPL"]) == {}


def test_refresh_writes_cache_with_mocked_network(tmp_path, monkeypatch):
    monkeypatch.setenv("FINPILOT_ENABLE_SENTIMENT", "1")
    monkeypatch.setenv("EODHD_API_KEY", "abc")
    monkeypatch.setattr(S, "_CACHE_PATH", tmp_path / "sentiment_cache.json")
    monkeypatch.setattr(S, "_RATE_LIMIT_SLEEP", 0.0)

    # Mock EODHD: AAPL positive, MSFT negative.
    def fake_get(url, params):
        sym = params["s"]
        val = 0.6 if sym.startswith("AAPL") else -0.6
        return {sym: [{"date": "2026-06-11", "normalized": val}]}

    monkeypatch.setattr(S, "_get", fake_get)
    out = S.refresh_sentiment_cache(["AAPL", "MSFT"])
    assert out["AAPL"] == 0.8  # (0.6+1)/2
    assert out["MSFT"] == 0.2  # (-0.6+1)/2
    # And the cache round-trips through compute_sentiment_factor.
    assert S.compute_sentiment_factor("AAPL") == 0.8
