import json
from pathlib import Path

from research.backfill_adjusted_price_cache import canonical_symbols, merge_history


def test_merge_history_preserves_raw_close_and_adds_adjusted_close(tmp_path: Path):
    path = tmp_path / "ABC.json"
    path.write_text('[{"date":"2026-01-01","close":10,"open":9}]', encoding="utf-8")

    changed = merge_history(
        path,
        [{"date": "2026-01-01", "close": 10, "adjusted_close": 9.5, "volume": 100}],
    )

    result = json.loads(path.read_text(encoding="utf-8"))
    assert changed == 1
    assert result[0]["close"] == 10
    assert result[0]["adjusted_close"] == 9.5
    assert result[0]["open"] == 9


def test_canonical_symbols_reads_csv(tmp_path: Path):
    csv_path = tmp_path / "signals.csv"
    csv_path.write_text(
        "symbol,scan_date\nABC,2026-01-01\nABC,2026-01-02\nXYZ,2026-01-01\n", encoding="utf-8"
    )

    assert canonical_symbols(csv_path) == {"ABC", "XYZ"}
