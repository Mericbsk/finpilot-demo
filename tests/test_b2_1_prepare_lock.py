import hashlib
import json
from pathlib import Path

import pytest
from scripts.b2_1_prepare_lock import (
    artifact_record,
    canonical_json,
    checked_path,
    code_record,
    disposition,
    export_schema,
    input_review,
    population_identity,
    project_export,
    static_import_evidence,
)


def test_artifact_record_is_integrity_not_provenance(tmp_path):
    source = tmp_path / "input.json"
    content = b'{"stored_score":42,"secret":"fixture-only"}'
    source.write_bytes(content)
    result = artifact_record(tmp_path, "input.json")
    assert result["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["historical_identity"] == "UNKNOWN"
    assert result["temporal_validity"] == "UNKNOWN"
    assert result["mtime_is_provenance"] is False
    assert "fixture-only" not in canonical_json(result)
    assert "stored_score" not in result
    assert source.read_bytes() == content
    assert sorted(path.name for path in tmp_path.iterdir()) == ["input.json"]


def test_absent_artifact_is_not_recovery_verdict(tmp_path):
    result = artifact_record(tmp_path, "absent.json")
    assert result == {"path": "absent.json", "availability": "NOT_FOUND", "sha256": None}
    assert "NOT_RECONSTRUCTIBLE" not in canonical_json(result)


def test_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError, match="inside"):
        checked_path(tmp_path, "../outside.json")
    with pytest.raises(ValueError, match="inside"):
        checked_path(tmp_path, str(tmp_path / "absolute.json"))


def test_canonical_json_is_order_independent_and_rejects_nan():
    assert canonical_json({"second": 2, "first": 1}) == canonical_json({"first": 1, "second": 2})
    assert json.loads(canonical_json({"status": "NOT_RUN"})) == {"status": "NOT_RUN"}
    with pytest.raises(ValueError):
        canonical_json({"invalid": float("nan")})


def test_source_inspection_does_not_import_or_execute():
    record = code_record("fixture.py", b"raise RuntimeError('must not run')\ndef producer(value):\n return round(value, 4)\n")
    assert record["symbols"][0]["round_expressions"] == ["round(value, 4)"]
    assert record["runtime_precision_identity"] == "UNKNOWN"


def test_export_schema_retains_population_without_recovery_values(tmp_path):
    source = tmp_path / "export.json"
    source.write_text(json.dumps({"date": "2000-01-01", "results": [{"symbol": "FAKE", "score_input": {"atr_pct": 42}}, {"error": "fixture"}]}))
    result = export_schema(source)
    assert result["population_count"] == 2
    assert result["population_filtered"] is False
    assert result["eligibility"] == "NOT_EVALUATED"
    assert result["score_input_schema"] == ["atr_pct"]
    assert "FAKE" not in canonical_json(result)
    assert "42" not in canonical_json(result)


def test_candidate_fixture_structure_only_not_scientific_suite():
    root = Path(__file__).resolve().parents[1]
    fixture = json.loads((root / "reports/b2_1_synthetic_fixtures_candidate_v3_2026-10-05.json").read_text())
    assert fixture["synthetic_gate"] == "NOT_RUN"
    assert fixture["contains_historical_rows"] is False
    assert fixture["authored_by"] == "NON_BLIND_CUSTODIAN"
    assert [case["id"] for case in fixture["cases"]] == [f"S{index:02d}" for index in range(1, 29)]
    for case in fixture["cases"]:
        subcases = case.get("subcases", [case])
        assert subcases
        assert all("input" in subcase and "expected" in subcase for subcase in subcases)
    assert [case["id"] for case in fixture["joint_squeeze_oracle_cases"]] == ["J01", "J02", "J03", "J04"]
    assert fixture["joint_oracle_specification"]["execution_status"] == "NOT_RUN"


def test_source_change_during_hashing_stops(tmp_path, monkeypatch):
    source = tmp_path / "changing.json"
    source.write_bytes(b"original")
    original_sha256 = hashlib.sha256

    class MutatingDigest:
        def __init__(self):
            self.digest = original_sha256()

        def update(self, chunk):
            self.digest.update(chunk)
            source.write_bytes(b"changed synthetic fixture length")

        def hexdigest(self):
            return self.digest.hexdigest()

    monkeypatch.setattr(hashlib, "sha256", MutatingDigest)
    with pytest.raises(RuntimeError, match="changed"):
        artifact_record(tmp_path, "changing.json")


def test_population_identity_preserves_unknowns_duplicates_and_order():
    rows = [{"symbol": "FAKE", "entry_ok": True}, {"symbol": "FAKE", "entry_ok": False},
            {"symbol": "OTHER"}, {"symbol": "THIRD", "entry_ok": "false"}, {"entry_ok": None}]
    result = population_identity({"results": rows})
    assert result["row_count"] == 5
    assert result["unique_valid_symbols"] == 3
    assert result["duplicate_symbol_counts"] == {"FAKE": 2}
    assert result["entry_ok_states"] == {"TRUE": 1, "FALSE": 1, "MISSING": 1, "MALFORMED": 2}
    assert result["entry_ok_is_complete"] is False
    assert result["missing_or_malformed_symbol_rows"] == 1
    assert result["historical_execution_identity"] == "UNKNOWN"
    assert result["population_membership_sha256"] != population_identity({"results": list(reversed(rows))})["population_membership_sha256"]
    assert rows[2] == {"symbol": "OTHER"}


def test_population_identity_rejects_non_object_rows():
    with pytest.raises(ValueError, match="every object row"):
        population_identity({"results": [None]})


def test_disposition_never_authorizes_candidate_and_keeps_unknowns():
    result = disposition({"path": "data/unknown.json", "sha256": "fake"}, {})
    assert result["evidence_classification"] == "UNRESOLVED"
    assert result["final_allowlist_status"] == "PENDING_HUMAN_REVIEW"
    assert result["blind_bundle_allowed"] is False
    candidate = disposition({"path": "data/daily_cache_h/FAKE.json", "sha256": "another"}, {})
    assert candidate["evidence_classification"] == "EXTERNAL_CANDIDATE"
    assert candidate["blind_bundle_allowed"] is False


def test_disposition_retains_duplicate_reference_without_dropping_row():
    seen = {}
    first = disposition({"path": "data/source.json", "sha256": "same"}, seen)
    second = disposition({"path": "data/copy.json", "sha256": "same"}, seen)
    assert first["evidence_classification"] == "UNRESOLVED"
    assert second["evidence_classification"] == "DUPLICATE_REFERENCE"
    assert second["duplicate_of"] == first["path"]
    assert second["blind_bundle_allowed"] is False


def test_research_result_is_excluded_without_reading_content():
    result = disposition({"path": "data/optuna_results.json", "sha256": "fixture"}, {})
    assert result["evidence_classification"] == "RESEARCH_RESULT_EXCLUDED"
    assert result["final_allowlist_status"] == "EXCLUDED_BY_PROTOCOL"
    assert result["blind_bundle_allowed"] is False
    duplicate = disposition({"path": "reports/research.json", "sha256": "same", "role": "RESEARCH_RESULT_EXCLUDED_FROM_BLIND_BUNDLE"}, {"same": "data/first.json"})
    assert duplicate["evidence_classification"] == "DUPLICATE_REFERENCE"
    assert duplicate["final_allowlist_status"] == "EXCLUDED_BY_PROTOCOL"


@pytest.mark.parametrize(("path", "role"), [
    ("data/shortlists/fixture.csv", "STORED_SCAN_OUTPUT_CANDIDATE"),
    ("data/daily_reports/fixture.json", "DOWNSTREAM_REPORT_CANDIDATE"),
    ("data/distribution/fixture.json", "EXPORT_OR_PUBLICATION_CANDIDATE"),
    ("data/unknown.json", "UNDETERMINED"),
])
def test_input_review_separates_possible_role_from_requiredness(path, role):
    original = disposition({"path": path, "sha256": "fixture"}, {})
    review = input_review(original)
    assert review["candidate_role"] == role
    assert review["requiredness"] == "UNDETERMINED_PENDING_MEMBER_REVIEW"
    assert review["historical_identity"] == "UNKNOWN"
    assert review["blind_bundle_allowed"] is False
    assert review["final_allowlist_status"] == "PENDING_HUMAN_REVIEW"
    assert original["evidence_classification"] == "UNRESOLVED"


def test_input_review_rejects_already_classified_records():
    with pytest.raises(ValueError, match="unresolved"):
        input_review(disposition({"path": "data/optuna_results.json", "sha256": "fixture"}, {}))


def test_project_export_preserves_every_row_order_and_missing_eligibility():
    source = {"scan_id": "fixture-envelope", "results": [
        {"symbol": "FAKE", "entry_ok": True, "score_input": {"fixture": 1}, "unapproved": "not-staged"},
        {"symbol": "FAKE", "entry_ok": False}, {"symbol": "OTHER"}, {"error": "fixture-only"},
    ]}
    before = canonical_json(source)
    stage = project_export(source, ["symbol", "entry_ok", "score_input"])
    assert len(stage["results"]) == 4
    assert stage["results"][2] == {"symbol": "OTHER"}
    assert stage["results"][3] == {}
    assert "unapproved" not in canonical_json(stage) and "scan_id" not in stage
    assert stage["results"][0]["score_input"] == {"fixture": 1}
    assert population_identity(source) == population_identity(stage)
    assert canonical_json(source) == before


def test_project_export_rejects_missing_membership_fields_and_invalid_allowlist():
    source = {"results": [{"symbol": "FAKE", "entry_ok": True}]}
    with pytest.raises(ValueError, match="population identity"):
        project_export(source, ["symbol"])
    with pytest.raises(ValueError, match="unique field"):
        project_export(source, ["symbol", "symbol"])
    with pytest.raises(ValueError, match="unique field"):
        project_export(source, [])


def test_static_import_evidence_traces_relative_members_and_initializers_without_execution():
    content = b"raise RuntimeError('must not execute')\nfrom . import feature\nfrom ..common import helper\nimport outside\nimportlib.import_module(secret_argument)\n"
    available = {"pkg/__init__.py", "pkg/sub/__init__.py", "pkg/sub/feature.py", "pkg/common.py"}
    result = static_import_evidence("pkg/sub/worker.py", content, available)
    assert result["imports"][0]["local_candidates"] == ["pkg/__init__.py", "pkg/sub/__init__.py", "pkg/sub/feature.py"]
    assert result["imports"][1]["local_candidates"] == ["pkg/__init__.py", "pkg/common.py"]
    assert result["imports"][2]["resolution"] == "EXTERNAL_OR_UNRESOLVED"
    assert all(item["runtime_resolution_verified"] is False for item in result["imports"])
    assert result["dynamic_loading_review"] == [{"line": 5, "call": "importlib.import_module"}]
    assert "secret_argument" not in canonical_json(result)


def test_static_import_evidence_preserves_invalid_relative_and_conditional_references():
    result = static_import_evidence("pkg/worker.py", b"from ... import impossible\nif False:\n import local\n", {"local.py"})
    assert result["imports"][0]["resolution"] == "INVALID_RELATIVE_REFERENCE"
    assert result["imports"][0]["local_candidates"] == []
    assert result["imports"][1]["local_candidates"] == ["local.py"]
    assert result["scope"] == "SYNTAX_REFERENCES_ALL_BRANCHES_NOT_RUNTIME_OR_SYMBOL_CLOSURE"

