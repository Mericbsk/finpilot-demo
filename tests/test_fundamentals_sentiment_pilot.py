from __future__ import annotations

import json

import fundamentals_sentiment_pilot as pilot


def test_honest_returns_uses_next_open_and_both_horizons(tmp_path, monkeypatch):
    price_dir = tmp_path / "price_cache"
    price_dir.mkdir()
    bars = [
        {"date": "2026-01-01", "open": 100, "close": 99},
        {"date": "2026-01-02", "open": 110, "close": 111},
        {"date": "2026-01-03", "open": 112, "close": 113},
        {"date": "2026-01-04", "open": 114, "close": 115},
        {"date": "2026-01-05", "open": 116, "close": 117},
        {"date": "2026-01-06", "open": 118, "close": 119},
        {"date": "2026-01-07", "open": 120, "close": 121},
        {"date": "2026-01-08", "open": 122, "close": 123},
        {"date": "2026-01-09", "open": 124, "close": 125},
        {"date": "2026-01-10", "open": 126, "close": 127},
        {"date": "2026-01-11", "open": 128, "close": 129},
        {"date": "2026-01-12", "open": 130, "close": 131},
        {"date": "2026-01-13", "open": 132, "close": 133},
        {"date": "2026-01-14", "open": 134, "close": 135},
        {"date": "2026-01-15", "open": 136, "close": 137},
        {"date": "2026-01-16", "open": 138, "close": 139},
        {"date": "2026-01-17", "open": 140, "close": 141},
        {"date": "2026-01-18", "open": 142, "close": 143},
        {"date": "2026-01-19", "open": 144, "close": 145},
        {"date": "2026-01-20", "open": 146, "close": 147},
        {"date": "2026-01-21", "open": 148, "close": 149},
    ]
    (price_dir / "TEST.json").write_text(json.dumps(bars), encoding="utf-8")
    monkeypatch.setattr(pilot, "PRICE_DIR", price_dir)

    result = pilot.honest_returns("TEST", "2026-01-01")

    assert result["c2c5_net"] == round((119 / 110 - 1) * 100 - pilot.COST_PCT, 4)
    assert result["c2c20_net"] == round((149 / 110 - 1) * 100 - pilot.COST_PCT, 4)


def test_news_features_excludes_future_rows(tmp_path, monkeypatch):
    news_dir = tmp_path / "news_cache"
    news_dir.mkdir()
    rows = [["2026-01-09", -0.5], ["2026-01-10", 0.5], ["2026-01-11", 1.0]]
    (news_dir / "TEST.json").write_text(json.dumps(rows), encoding="utf-8")
    monkeypatch.setattr(pilot, "NEWS_DIR", news_dir)

    result = pilot.news_features("TEST", "2026-01-10")

    assert result["news_count_5d"] == 2
    assert result["news_count_20d"] == 2
    assert result["news_sentiment_5d"] == 0.0


def test_current_fundamentals_are_not_used_without_snapshot(tmp_path, monkeypatch):
    fundamentals = tmp_path / "fundamentals_cache.json"
    fundamentals.write_text(json.dumps({"TEST": {"short_pct": 12.0}}), encoding="utf-8")
    monkeypatch.setattr(pilot, "FUNDAMENTALS", fundamentals)

    assert pilot._point_in_time_fundamentals(None) == {}
    assert pilot._point_in_time_fundamentals("2026-01-01")["TEST"]["short_pct"] == 12.0
