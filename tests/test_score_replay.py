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


def test_score_replay_accepts_production_component_total_alias(tmp_path: Path):
    path = tmp_path / "production_export.csv"
    path.write_text(
        "symbol,timestamp,regime,direction,score,filter_score,alignment_ratio,momentum_ratio,vol_regime,volume_spike,price_momentum,trend_strength,score_component_total\n"
        "AAPL,2026-08-01T13:30:00Z,True,True,3,3,1,1,0,True,True,True,16\n",
        encoding="utf-8",
    )

    result = replay(path)

    assert result["status"] == "pass"
    assert result["compared"] == 1


def test_score_replay_accepts_scan_export_json(tmp_path: Path):
    path = tmp_path / "scan_export.json"
    path.write_text(
        '{"results":[{"symbol":"AAPL","timestamp":"2026-08-01T13:30:00Z","regime":true,"direction":true,"score":3,"filter_score":3,"alignment_ratio":1,"momentum_ratio":1,"vol_regime":0,"volume_spike":true,"price_momentum":true,"trend_strength":true,"score_component_total":16}]}',
        encoding="utf-8",
    )

    result = replay(path)

    assert result["status"] == "pass"
    assert result["compared"] == 1


def test_score_replay_checks_persisted_breakdown_total(tmp_path: Path):
    path = tmp_path / "scan_export.json"
    path.write_text(
        '{"results":[{"symbol":"AAPL","timestamp":"2026-08-01T13:30:00Z","regime":true,"direction":true,"score":3,"filter_score":3,"alignment_ratio":1,"momentum_ratio":1,"vol_regime":0,"volume_spike":true,"price_momentum":true,"trend_strength":true,"score_component_total":16,"score_component_breakdown":{"total":16}}]}',
        encoding="utf-8",
    )

    result = replay(path)

    assert result["persisted_breakdown_compared"] == 1
    assert result["persisted_breakdown_mismatch_count"] == 0


def test_score_replay_accepts_nested_score_input_contract(tmp_path: Path):
    path = tmp_path / "nested_export.json"
    path.write_text(
        '{"results":[{"symbol":"AAPL","timestamp":"2026-08-01T13:30:00Z","score_input":{"regime":true,"direction":true,"score":3,"filter_score":3,"alignment_ratio":1,"momentum_ratio":1,"vol_regime":0,"volume_spike":true,"price_momentum":true,"trend_strength":true},"score_feature_flags":{"squeeze_factor":false,"edgar_catalyst":false,"lottery_fade":false,"overnight_gap":false},"recommendation_score":16}]}',
        encoding="utf-8",
    )

    result = replay(path)

    assert result["status"] == "pass"
    assert result["compared"] == 1
