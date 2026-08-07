from pathlib import Path

from research.candidate_pipeline import _candidate_scorecard


def test_candidate_scorecard_reports_cost_scenarios(tmp_path: Path):
    csv_path = tmp_path / "rows.csv"
    csv_path.write_text(
        "symbol,scan_ts,scan_date,price,atr_pct_real,entry_ok,regime,direction,gap_pct,rvol,squeeze_factor,composite_score,dist_52w_high\n"
        "AAPL,2026-01-01T10:00:00Z,2026-01-01,100,2,True,True,True,0,1,0,40,0.5\n",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "AAPL.json").write_text("[]", encoding="utf-8")

    result = _candidate_scorecard(csv_path, cache)

    assert set(result["cost_scenarios"]) == {"low", "base", "high"}
    assert result["methodology"]["mfe_is_not_pnl"] is True
