from __future__ import annotations

import json
from pathlib import Path

import pytest
from research.sec_companyfacts import (
    append_snapshot,
    load_snapshot_records,
    normalize_companyfacts,
    pit_latest_facts,
)


@pytest.fixture
def companyfacts_payload() -> dict:
    return {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "label": "Revenues",
                    "description": "Revenue",
                    "units": {
                        "USD": [
                            {
                                "start": "2025-01-01",
                                "end": "2025-12-31",
                                "val": 100,
                                "accn": "0000000000-26-000001",
                                "filed": "2026-02-15",
                                "form": "10-K",
                            }
                        ]
                    },
                }
            }
        }
    }


def test_normalize_companyfacts_preserves_pit_fields(companyfacts_payload):
    records = normalize_companyfacts(
        companyfacts_payload,
        cik="320193",
        retrieved_at="2026-08-05T12:00:00+00:00",
    )

    assert len(records) == 1
    record = records[0]
    assert record["observation_date"] == "2025-12-31"
    assert record["publication_date"] == "2026-02-15"
    assert record["source"] == "SEC EDGAR companyfacts"
    assert record["accn"] == "0000000000-26-000001"
    assert record["cik"] == "0000320193"


def test_append_snapshot_is_append_only(tmp_path: Path, companyfacts_payload):
    records = normalize_companyfacts(companyfacts_payload, cik="320193", retrieved_at="t1")
    path = tmp_path / "sec_companyfacts.jsonl"

    first = append_snapshot(path, records, retrieved_at="t1")
    second = append_snapshot(path, records, retrieved_at="t2")
    lines = path.read_text(encoding="utf-8").splitlines()

    assert first["snapshot_id"] == second["snapshot_id"]
    assert len(lines) == 2
    assert json.loads(lines[0])["retrieved_at"] == "t1"
    assert json.loads(lines[1])["retrieved_at"] == "t2"


def test_append_snapshot_rejects_empty_records(tmp_path: Path):
    with pytest.raises(ValueError, match="empty"):
        append_snapshot(tmp_path / "facts.jsonl", [])


def test_pit_latest_facts_excludes_future_filing_and_selects_latest(
    tmp_path: Path, companyfacts_payload
):
    records = normalize_companyfacts(companyfacts_payload, cik="320193", retrieved_at="t1")
    later = dict(records[0], value=200, publication_date="2026-03-01", retrieved_at="t2")
    path = tmp_path / "facts.jsonl"
    append_snapshot(path, records, retrieved_at="t1")
    append_snapshot(path, [later], retrieved_at="t2")

    loaded = load_snapshot_records(path)
    before_later = pit_latest_facts(loaded, cik="320193", as_of_date="2026-02-28")
    after_later = pit_latest_facts(loaded, cik="320193", as_of_date="2026-03-02")

    assert before_later[("Revenues", "USD")]["value"] == 100
    assert after_later[("Revenues", "USD")]["value"] == 200


def test_pit_latest_facts_can_preserve_observation_periods(companyfacts_payload):
    records = normalize_companyfacts(companyfacts_payload, cik="320193", retrieved_at="t1")
    later_period = dict(records[0], observation_date="2026-12-31", value=300)

    selected = pit_latest_facts(
        records + [later_period],
        cik="320193",
        as_of_date="2027-01-01",
        by_observation_date=True,
    )

    assert len(selected) == 2
    assert selected[("Revenues", "USD", "2025-12-31")]["value"] == 100
    assert selected[("Revenues", "USD", "2026-12-31")]["value"] == 300
