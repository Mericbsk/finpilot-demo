from pathlib import Path

from research.build_score_replay_input import build


def test_build_selects_latest_suggestion_and_nearest_vol_regime(tmp_path: Path):
    suggestions = tmp_path / "suggestions"
    suggestions.mkdir()
    (suggestions / "suggestions_2026.csv").write_text(
        "symbol,price,timestamp,regime,direction,score,filter_score,alignment_ratio,momentum_ratio,volume_spike,price_momentum,trend_strength,recommendation_score\n"
        "AAPL,100,2026-01-01 09:00,True,True,3,2,1,1,True,True,False,10\n"
        "AAPL,101,2026-01-01 10:00,True,True,3,3,1,1,True,True,True,11\n",
        encoding="utf-8",
    )
    canonical = tmp_path / "canonical.csv"
    canonical.write_text(
        "symbol,scan_date,scan_ts,vol_regime\n" "AAPL,2026-01-01,2026-01-01 10:00,2\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.csv"

    result = build(suggestions, canonical, output)

    assert result["selected_rows"] == 1
    assert result["duplicate_symbol_days"] == 1
    assert result["conflict_symbol_days"] == 1
    assert output.read_text(encoding="utf-8").splitlines()[1].endswith(",2")
