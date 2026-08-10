import json
from pathlib import Path

from research.price_cache_integrity_audit import audit_symbol, run


def test_audit_flags_large_close_jump(tmp_path: Path):
    (tmp_path / "ABC.json").write_text(
        json.dumps(
            [
                {"date": "2026-01-01", "close": 10},
                {"date": "2026-01-02", "close": 100},
            ]
        ),
        encoding="utf-8",
    )

    result = audit_symbol(tmp_path / "ABC.json", 50.0)

    assert result["large_jump_count"] == 1
    assert result["jumps"][0]["change_pct"] == 900.0


def test_audit_reports_clean_cache(tmp_path: Path):
    (tmp_path / "ABC.json").write_text(
        '[{"date":"2026-01-01","close":10},{"date":"2026-01-02","close":10.5}]',
        encoding="utf-8",
    )

    result = run(tmp_path)

    assert result["symbols_scanned"] == 1
    assert result["symbols_with_large_jumps"] == 0


def test_audit_can_use_adjusted_close(tmp_path: Path):
    path = tmp_path / "ABC.json"
    path.write_text(
        '[{"date":"2026-01-01","close":100,"adjusted_close":10},'
        '{"date":"2026-01-02","close":200,"adjusted_close":11}]',
        encoding="utf-8",
    )

    result = audit_symbol(path, 50.0, "adjusted_close")

    assert result["large_jump_count"] == 0
    assert result["price_field"] == "adjusted_close"
