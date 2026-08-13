from __future__ import annotations

import json

from research.data_readiness_audit import build_audit, snapshot_manifest


def test_audit_does_not_treat_current_cache_as_immutable(tmp_path):
    price_cache = tmp_path / "data" / "price_cache"
    price_cache.mkdir(parents=True)
    (price_cache / "AAA.json").write_text(
        json.dumps([{"date": "2026-01-01", "close": 10.0}]), encoding="utf-8"
    )

    result = build_audit(tmp_path)

    assert result["inputs"]["price_cache"]["available"] is True
    assert result["inputs"]["price_cache"]["immutable_snapshot"] is False
    assert result["gates"]["P1_data_reliability"] == "BLOCKED"


def test_snapshot_manifest_is_explicitly_not_a_bar_snapshot(tmp_path):
    cache = tmp_path / "price_cache"
    cache.mkdir()
    (cache / "AAA.json").write_text("[]", encoding="utf-8")
    output = tmp_path / "manifest.json"

    result = snapshot_manifest(cache, output)

    assert result["kind"] == "hash_manifest"
    assert result["restatement_comparison_ready"] is False
    assert output.exists()
