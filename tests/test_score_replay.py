from pathlib import Path

from research.score_replay import replay


def test_score_replay_reports_missing_fields_without_inference(tmp_path: Path):
    path = tmp_path / "incomplete.csv"
    path.write_text("symbol,score\nAAPL,3\n", encoding="utf-8")

    result = replay(path)

    assert result["status"] == "insufficient_data"
    assert "recommendation_score" in result["missing_fields"]


def test_score_replay_passes_matching_complete_row(tmp_path: Path):
    path = tmp_path / "complete.csv"
    path.write_text(
        "symbol,timestamp,regime,direction,score,filter_score,alignment_ratio,momentum_ratio,vol_regime,volume_spike,price_momentum,trend_strength,recommendation_score\n"
        "AAPL,2026-08-01T13:30:00Z,True,True,3,3,1,1,0,True,True,True,16\n",
        encoding="utf-8",
    )

    result = replay(path)

    assert result["status"] == "pass"
    assert result["compared"] == 1
