"""Fixture-scoped checks for the read-only B2-AUTH evidence collector."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture()
def audit():
    path = Path(__file__).resolve().parents[1] / "scripts/b2_auth_readonly_audit.py"
    spec = importlib.util.spec_from_file_location("b2_auth_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reads_exclude_comments_writes_and_unrelated_get(audit):
    text = """import os
# os.getenv("FINPILOT_ENABLE_COMMENT", "1")
os.environ["FINPILOT_ENABLE_WRITE"] = "1"
settings.get("FINPILOT_ENABLE_OTHER", "1")
os.getenv("FINPILOT_ENABLE_REAL", "0")
os.environ["FINPILOT_ENABLE_REQUIRED"]
"""
    reads, state = audit.source_reads(text)
    assert state == "PARSED"
    assert [read["flag"] for read in reads] == ["FINPILOT_ENABLE_REAL", "FINPILOT_ENABLE_REQUIRED"]


def test_aliases_keywords_and_dynamic_default(audit):
    reads, _ = audit.source_reads("""from os import getenv as env
import os as operating
env(key="FINPILOT_ENABLE_ONE", default="1")
operating.environ.get("FINPILOT_ENABLE_TWO", fallback)
""")
    assert reads[0]["default"] == "1"
    assert reads[1]["default_expression"] == "DYNAMIC"


def test_config_is_sanitized_not_loaded_and_runtime_unknown(audit, tmp_path, monkeypatch):
    config = tmp_path / ".env"
    config.write_text(
        'FINPILOT_ENABLE_TEST="1"\nSECRET=private-fixture\n'
        "FINPILOT_ENABLE_BAD=private-fixture\nFINPILOT_ENABLE_EXPAND=${SECRET}\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("FINPILOT_ENABLE_TEST", raising=False)
    state = audit.build_inventory(tmp_path, process_env={})
    serialized = json.dumps(state)
    assert "private-fixture" not in serialized
    assert "${SECRET}" not in serialized
    assert "FINPILOT_ENABLE_TEST" not in audit.os.environ
    values = {entry["flag"]: entry for entry in state["flags"]}
    assert values["FINPILOT_ENABLE_TEST"]["local_file_value"] == "1"
    assert values["FINPILOT_ENABLE_TEST"]["audit_process_value"] == "UNSET"
    assert all(entry["production_runtime_value"] == "UNKNOWN" for entry in values.values())


def test_determinism_no_import_no_source_mutation(audit, tmp_path):
    scanner = tmp_path / "scanner"
    scanner.mkdir()
    source = scanner / "fixture.py"
    source.write_text(
        'raise RuntimeError("MUST NOT EXECUTE")\n'
        'import os\nos.getenv("FINPILOT_ENABLE_TEST", "0")\n',
        encoding="utf-8",
    )
    before = source.read_bytes()
    first = audit.build_inventory(tmp_path, process_env={})
    second = audit.build_inventory(tmp_path, process_env={})
    assert first == second
    assert source.read_bytes() == before
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")) == [
        "scanner",
        "scanner/fixture.py",
    ]


def test_log_mention_is_not_authorization(audit, tmp_path):
    governance = tmp_path / "docs/governance"
    governance.mkdir(parents=True)
    (governance / "decision-log.md").write_text(
        "FINPILOT_ENABLE_TEST ON approved? pending\n", encoding="utf-8"
    )
    state = audit.build_inventory(tmp_path, process_env={"FINPILOT_ENABLE_TEST": "1"})
    entry = state["flags"][0]
    assert entry["decision_log_literal_mentions"] == [1]
    assert entry["authorization"] == "REQUIRES_HUMAN_RECORD_REVIEW"
    assert state["production_action"] == "NONE"


def test_syntax_errors_are_not_silently_treated_as_no_readers(audit):
    reads, state = audit.source_reads('if :\n os.getenv("FINPILOT_ENABLE_TEST")')
    assert reads == []
    assert state == "SYNTAX_ERROR"


def test_associated_controls_are_in_scope(audit):
    reads, state = audit.source_reads("""import os
os.getenv("FINPILOT_DRL_GATE", "0")
os.getenv("FINPILOT_INSTRUMENT_BASELINE", "0")
os.getenv("FINPILOT_ALERT_ON_SCAN", "1")
""")
    assert state == "PARSED"
    assert [read["flag"] for read in reads] == [
        "FINPILOT_DRL_GATE",
        "FINPILOT_INSTRUMENT_BASELINE",
        "FINPILOT_ALERT_ON_SCAN",
    ]
