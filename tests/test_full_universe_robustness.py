from full_universe_robustness import dedup_symbol_day


def test_dedup_symbol_day_uses_earliest_scan_by_default():
    rows = [
        {"symbol": "ABC", "scan_date": "2026-07-27", "scan_ts": "2026-07-27T14:00:00Z"},
        {"symbol": "ABC", "scan_date": "2026-07-27", "scan_ts": "2026-07-27T13:00:00Z"},
        {"symbol": "XYZ", "scan_date": "2026-07-27", "scan_ts": "2026-07-27T13:30:00Z"},
    ]

    result = dedup_symbol_day(rows)

    assert [row["scan_ts"] for row in result] == [
        "2026-07-27T13:00:00Z",
        "2026-07-27T13:30:00Z",
    ]


def test_dedup_symbol_day_supports_latest_sensitivity_policy():
    rows = [
        {"symbol": "ABC", "scan_date": "2026-07-27", "scan_ts": "2026-07-27T13:00:00Z"},
        {"symbol": "ABC", "scan_date": "2026-07-27", "scan_ts": "2026-07-27T14:00:00Z"},
    ]

    result = dedup_symbol_day(rows, policy="latest")

    assert result[0]["scan_ts"] == "2026-07-27T14:00:00Z"
