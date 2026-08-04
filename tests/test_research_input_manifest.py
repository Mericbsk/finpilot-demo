from pathlib import Path

from scripts.research_input_manifest import build_manifest, csv_summary


def test_csv_summary_reports_duplicates_missingness_and_date_range(tmp_path: Path):
    path = tmp_path / "signals.csv"
    path.write_text(
        "symbol,scan_date,scan_ts,score\n"
        "AAA,2026-07-01,2026-07-01T13:00:00Z,1\n"
        "AAA,2026-07-01,2026-07-01T14:00:00Z,\n"
        "BBB,2026-07-02,2026-07-02T13:00:00Z,2\n",
        encoding="utf-8",
    )

    result = csv_summary(path)

    assert result["rows"] == 3
    assert result["keys"]["duplicate_symbol_day_keys"] == 1
    assert result["keys"]["duplicate_rows"] == 1
    assert result["missingness"]["score"]["count"] == 1
    assert result["date_range"] == {"min": "2026-07-01", "max": "2026-07-02"}


def test_manifest_marks_research_only_and_hashes_file(tmp_path: Path):
    path = tmp_path / "sample.csv"
    path.write_text("symbol,scan_date\nAAA,2026-07-01\n", encoding="utf-8")

    manifest = build_manifest((path,))

    assert manifest["research_only"] is True
    assert manifest["inputs"][0]["status"] == "available"
    assert len(manifest["inputs"][0]["sha256"]) == 64
