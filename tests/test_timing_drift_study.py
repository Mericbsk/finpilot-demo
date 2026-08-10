from math import isclose
from pathlib import Path

from research.timing_drift_study import (
    _summary,
    build_observations,
    deduplicate_symbol_day,
    load_bars,
)


def test_deduplicate_symbol_day_keeps_earliest_scan():
    rows = [
        {"symbol": "ABC", "scan_date": "2026-07-01", "scan_ts": "2026-07-01T14:00:00Z"},
        {"symbol": "ABC", "scan_date": "2026-07-01", "scan_ts": "2026-07-01T13:00:00Z"},
        {"symbol": "XYZ", "scan_date": "2026-07-01", "scan_ts": "2026-07-01T13:30:00Z"},
    ]

    result = deduplicate_symbol_day(rows)

    assert [row["scan_ts"] for row in result] == [
        "2026-07-01T13:00:00Z",
        "2026-07-01T13:30:00Z",
    ]


def test_load_bars_rejects_missing_open_and_keeps_daily_ohlc(tmp_path: Path):
    (tmp_path / "ABC.json").write_text(
        '[{"date":"2026-07-01","open":10,"high":11,"low":9,"close":10.5},'
        '{"date":"2026-07-02","high":12,"low":10,"close":11}]',
        encoding="utf-8",
    )

    bars = load_bars(tmp_path, "ABC")

    assert len(bars) == 1
    assert bars[0]["close"] == 10.5


def test_summary_reports_distribution_not_only_mean():
    summary = _summary([-1.0, 0.5, 2.0, 3.0])

    assert summary["n"] == 4
    assert summary["median_pct"] == 1.25
    assert summary["positive_rate"] == 0.75


def test_next_close_uses_the_close_after_the_entry_day(tmp_path: Path):
    (tmp_path / "ABC.json").write_text(
        '[{"date":"2026-07-01","open":10,"high":11,"low":9,"close":10},'
        '{"date":"2026-07-02","open":11,"high":12,"low":10,"close":12},'
        '{"date":"2026-07-03","open":13,"high":14,"low":12,"close":15},'
        '{"date":"2026-07-04","open":15,"high":16,"low":14,"close":16}]',
        encoding="utf-8",
    )

    rows, inventory = build_observations(
        [
            {
                "symbol": "ABC",
                "scan_date": "2026-07-01",
                "scan_ts": "2026-07-01T15:00:00Z",
                "recorded_price": 10.0,
                "direction": False,
                "entry_ok": True,
            }
        ],
        tmp_path,
        [1],
        (),
    )

    assert inventory["resolved"] == 1
    assert rows[0]["returns"]["1"]["next_close"] == 25.0


def test_direction_false_does_not_reverse_raw_return(tmp_path: Path):
    (tmp_path / "ABC.json").write_text(
        '[{"date":"2026-07-01","open":10,"high":11,"low":9,"close":10},'
        '{"date":"2026-07-02","open":11,"high":12,"low":10,"close":12},'
        '{"date":"2026-07-03","open":13,"high":14,"low":12,"close":15}]',
        encoding="utf-8",
    )

    rows, _ = build_observations(
        [
            {
                "symbol": "ABC",
                "scan_date": "2026-07-01",
                "scan_ts": "",
                "recorded_price": 10.0,
                "direction": False,
                "entry_ok": True,
            }
        ],
        tmp_path,
        [1],
        (),
    )

    assert isclose(rows[0]["returns"]["1"]["signal_close"], 20.0)


def test_benchmark_return_uses_the_same_entry_point(tmp_path: Path):
    bars = (
        '[{"date":"2026-07-01","open":100,"high":101,"low":99,"close":100},'
        '{"date":"2026-07-02","open":110,"high":111,"low":109,"close":120},'
        '{"date":"2026-07-03","open":120,"high":121,"low":119,"close":130}]'
    )
    (tmp_path / "ABC.json").write_text(bars, encoding="utf-8")
    (tmp_path / "SPY.json").write_text(bars, encoding="utf-8")

    rows, _ = build_observations(
        [
            {
                "symbol": "ABC",
                "scan_date": "2026-07-01",
                "scan_ts": "",
                "recorded_price": 100.0,
                "direction": True,
                "entry_ok": True,
            }
        ],
        tmp_path,
        [1],
        ("SPY",),
    )

    assert isclose(rows[0]["benchmark_returns"]["1"]["SPY"]["signal_close"], 20.0)
