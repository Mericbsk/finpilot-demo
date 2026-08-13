"""Contract test for the close-to-close export fields (Level B proposal).

Verifies that resolve_and_features now emits realized close-to-close returns
(c2c_1d, c2c_5d) and MAE (mae_t5) alongside the existing MFE field
(resolved_pct_t5), and that the MFE field is unchanged.
"""

from __future__ import annotations

from fetch_full_universe_and_retest import resolve_and_features


def _bars() -> list[dict]:
    # 8 bars; signal at index 2 (2026-01-03). Entry = close of signal bar = 100.
    # Forward bars T+1..T+5 are indices 3..7.
    closes = [98.0, 99.0, 100.0, 101.0, 104.0, 99.0, 103.0, 106.0]
    dates = [f"2026-01-0{i+1}" for i in range(8)]
    bars = []
    for d, c in zip(dates, closes, strict=False):
        bars.append(
            {
                "date": d,
                "open": c - 0.5,
                "high": c + 2.0,  # high is always close + 2
                "low": c - 3.0,  # low is always close - 3
                "close": c,
                "volume": 1000,
            }
        )
    return bars


def test_close_to_close_and_mfe_are_distinct() -> None:
    bars = _bars()
    out = resolve_and_features(100.0, "2026-01-03", bars)
    assert out is not None
    # MFE: max high over T+1..T+5 = close(106)+2 = 108 -> +8%
    assert abs(out["resolved_pct_t5"] - 8.0) < 1e-6
    # c2c_1d: close T+1 = 101 -> +1%
    assert abs(out["c2c_1d"] - 1.0) < 1e-6
    # c2c_5d: close T+5 = 106 -> +6%
    assert abs(out["c2c_5d"] - 6.0) < 1e-6
    # MAE: min low over T+1..T+5 = close(99)-3 = 96 -> -4%
    assert abs(out["mae_t5"] - (-4.0)) < 1e-6
    # MFE (8%) must differ from c2c_5d (6%) — they measure different things
    assert out["resolved_pct_t5"] != out["c2c_5d"]


def test_existing_fields_preserved() -> None:
    bars = _bars()
    out = resolve_and_features(100.0, "2026-01-03", bars)
    # All pre-existing fields still present
    for key in (
        "resolved_pct_t5",
        "resolved_pct_1d",
        "gap_pct",
        "rvol",
        "atr_pct_real",
        "dist_52w_high",
    ):
        assert key in out
