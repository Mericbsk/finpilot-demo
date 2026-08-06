"""Research-only SEC EDGAR CompanyFacts adapter with append-only snapshots.

CompanyFacts is normalized here, not joined into scanner features. Each fetch is
stored as a new JSONL record so later SEC restatements cannot overwrite the
historical retrieval evidence used by a PIT research run.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

SEC_BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


def normalize_companyfacts(
    payload: dict[str, Any],
    *,
    cik: str,
    retrieved_at: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten SEC CompanyFacts into PIT-ready fact observations."""
    facts = payload.get("facts", {})
    retrieved = retrieved_at or datetime.now(UTC).isoformat()
    records: list[dict[str, Any]] = []
    for taxonomy, taxonomy_facts in facts.items():
        for tag, definition in taxonomy_facts.items():
            label = definition.get("label")
            description = definition.get("description")
            for unit, observations in definition.get("units", {}).items():
                for observation in observations:
                    if not observation.get("filed") or "val" not in observation:
                        continue
                    records.append(
                        {
                            "cik": str(cik).zfill(10),
                            "taxonomy": taxonomy,
                            "tag": tag,
                            "unit": unit,
                            "value": observation["val"],
                            "observation_date": observation.get("end"),
                            "observation_start": observation.get("start"),
                            "publication_date": observation["filed"],
                            "form": observation.get("form"),
                            "accn": observation.get("accn"),
                            "frame": observation.get("frame"),
                            "label": label,
                            "description": description,
                            "source": "SEC EDGAR companyfacts",
                            "source_url": SEC_BASE_URL.format(cik=int(cik)),
                            "retrieved_at": retrieved,
                        }
                    )
    return records


def snapshot_hash(records: list[dict[str, Any]]) -> str:
    """Return a stable hash for one normalized retrieval payload."""
    encoded = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def append_snapshot(
    path: Path,
    records: list[dict[str, Any]],
    *,
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    """Append one immutable retrieval envelope to a JSONL snapshot ledger."""
    if not records:
        raise ValueError("cannot snapshot an empty SEC CompanyFacts response")
    retrieved = retrieved_at or datetime.now(UTC).isoformat()
    envelope = {
        "snapshot_id": snapshot_hash(records),
        "retrieved_at": retrieved,
        "source": "SEC EDGAR companyfacts",
        "record_count": len(records),
        "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n")
    return envelope


def load_snapshot_records(path: Path) -> list[dict[str, Any]]:
    """Read all normalized records from an append-only SEC JSONL ledger."""
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(envelope, dict):
            records.extend(
                record for record in envelope.get("records", []) if isinstance(record, dict)
            )
    return records


def pit_latest_facts(
    records: list[dict[str, Any]],
    *,
    cik: str,
    as_of_date: str,
    by_observation_date: bool = False,
) -> dict[tuple[str, ...], dict[str, Any]]:
    """Select latest filed facts known by an as-of date.

    The default key is ``(tag, unit)`` and means the latest known value. Set
    ``by_observation_date`` for period-series work, where each observation
    period must remain distinct across later filings or restatements.

    CompanyFacts cannot recover a pre-collection original if the SEC has
    already replaced it with a restated history before the first snapshot.
    """
    normalized_cik = str(cik).zfill(10)
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        if record.get("cik") != normalized_cik:
            continue
        publication_date = record.get("publication_date")
        if not publication_date or publication_date > as_of_date:
            continue
        key_parts = [str(record.get("tag", "")), str(record.get("unit", ""))]
        if by_observation_date:
            key_parts.append(str(record.get("observation_date", "")))
        key = tuple(key_parts)
        current = selected.get(key)
        if current is None or publication_date > current.get("publication_date", ""):
            selected[key] = record
    return selected


def fetch_companyfacts(cik: str, *, user_agent: str, timeout: int = 30) -> dict[str, Any]:
    """Fetch one SEC CompanyFacts payload; caller decides when to snapshot it."""
    if not user_agent.strip():
        raise ValueError("SEC requests require a descriptive User-Agent")
    normalized_cik = str(cik).strip().zfill(10)
    if not normalized_cik.isdigit() or len(normalized_cik) != 10:
        raise ValueError("cik must be a numeric SEC CIK")
    request = Request(  # noqa: S310
        SEC_BASE_URL.format(cik=int(normalized_cik)),
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310  # nosec B310
        return json.load(response)
