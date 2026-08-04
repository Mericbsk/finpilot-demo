from __future__ import annotations

import json

import shadow_scorecard as scorecard


def _bars(count: int = 25) -> list[dict]:
    bars = []
    for index in range(count):
        close = 100.0 + index
        bars.append(
            {
                "date": f"2026-01-{index + 1:02d}",
                "open": close,
                "high": close + 2.0,
                "low": close - 1.0,
                "close": close,
            }
        )
    return bars


def test_forward_return_and_percentiles():
    bars = _bars()
    assert scorecard.forward_return(bars, 5, 3) == (107.0 / 105.0 - 1.0) * 100.0
    assert scorecard.percentile_summary([1.0, 2.0, 3.0, 4.0, 5.0]) == {
        "p10": 1.4,
        "median": 3.0,
        "p90": 4.6,
    }


def test_control_score_has_forward_and_excess(monkeypatch, tmp_path):
    price_dir = tmp_path / "price_cache"
    price_dir.mkdir()
    bars = _bars()
    (price_dir / "ABC.json").write_text(json.dumps(bars), encoding="utf-8")
    (price_dir / "SPY.json").write_text(json.dumps(bars), encoding="utf-8")
    monkeypatch.setattr(scorecard, "PRICE_DIR", str(price_dir))
    scorecard._price_cache.clear()

    row = {
        "symbol": "ABC",
        "timestamp": "2026-01-03 12:00",
        "selection_eligible": False,
        "entry_ok": False,
        "reject_reason": ["liquidity_gate"],
        "dollar_adv": 2_000_000,
        "data_quality_tier": "Tier 1",
    }
    result = scorecard.score_signal(row, horizons=[1, 3], benchmark_symbol="SPY")
    assert result["_status"] == "scored"
    assert result["is_control"] is True
    assert "forward_ret_1" in result
    assert "forward_ret_atr_3" in result
    assert result["spy_excess_3"] == 0.0
    assert result["segment_adv"] == "1m-10m"
    assert result["reject_reason"] == "liquidity_gate"


def test_selected_and_control_summary_are_separate():
    rows = [
        {"forward_ret_5": 5.0, "forward_ret_atr_5": 1.0, "spy_excess_5": 2.0, "is_control": False},
        {
            "forward_ret_5": -1.0,
            "forward_ret_atr_5": -0.2,
            "spy_excess_5": -2.0,
            "is_control": True,
            "reject_reason": "regime_gate",
        },
    ]
    summary = scorecard.summarize(rows)
    assert summary["selected"]["n"] == 1
    assert summary["control"]["n"] == 1
    assert summary["control_by_reason"]["regime_gate"]["n"] == 1
