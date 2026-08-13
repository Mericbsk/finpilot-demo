import csv

from alpha_v2_research_runner import load_rows


def test_alpha_v2_accepts_canonical_scan_date(tmp_path):
    source = tmp_path / "enriched.csv"
    fields = ["symbol", "scan_date", "resolved_pct_t5"]
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"symbol": "AAA", "scan_date": "2026-01-01", "resolved_pct_t5": "5"})

    rows = load_rows(source)

    assert len(rows) == 1
    assert rows[0]["scan_date"] == "2026-01-01"
