"""Controller self-audit / regression tests (Master spec v0.2 invariants).

READ-ONLY tests with temporary fixtures; real locked artifacts are NOT touched.
These tests prove the controller carries governance state reliably; they do NOT
produce scientific findings. Each test maps to a locked invariant.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "research_governance_controller.py"


def load_controller():
    spec = importlib.util.spec_from_file_location("rgc", SPEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def ctl():
    return load_controller()


# --- Test 1: UNKNOWN preservation (verdict absent -> UNKNOWN, never FALSE) ---
def test_unknown_never_becomes_false(ctl, tmp_path, monkeypatch):
    # a result JSON with NO verdict-ish key at all
    rj = tmp_path / "r.json"
    rj.write_text(json.dumps({"n": 5, "foo": 1}), encoding="utf-8")
    spec = {
        "prereg": None,
        "runner": None,
        "result_json": None,
        "report": None,
        "verification": None,
    }
    # point the controller's ROOT at tmp so relative path resolves
    monkeypatch.setattr(ctl, "ROOT", tmp_path)
    spec["result_json"] = "r.json"
    st = ctl.derive_line_state("T-UNKNOWN", spec)
    assert st["scientific_verdict"] == "UNKNOWN"
    assert st["scientific_verdict"] not in ("FALSE", "NOT_SUPPORTED", "FAILED")


# --- Test 2: NOT_FOUND is not NOT_PERFORMED ---
def test_not_found_is_not_not_performed(ctl, tmp_path, monkeypatch):
    monkeypatch.setattr(ctl, "ROOT", tmp_path)
    spec = {
        "prereg": "missing_prereg.md",
        "runner": None,
        "result_json": "missing_result.json",
        "report": None,
        "verification": None,
    }
    st = ctl.derive_line_state("T-NOTFOUND", spec)
    # lifecycle is UNKNOWN (insufficient provenance), never a fabricated "NOT_PERFORMED"
    assert st["lifecycle_state"] == "UNKNOWN"
    assert "prereg" in st["missing_artifacts"] and "result_json" in st["missing_artifacts"]
    # and the verdict must be UNKNOWN, not a negative finding
    assert st["scientific_verdict"] == "UNKNOWN"


# --- Test 3: conflict is surfaced, never resolved by the controller ---
def test_conflict_surfaced_not_resolved(ctl, tmp_path, monkeypatch):
    monkeypatch.setattr(ctl, "ROOT", tmp_path)
    # artifact exists but lifecycle derivation yields UNKNOWN -> conflict path
    spec = {
        "prereg": None,
        "runner": None,
        "result_json": "exists.json",
        "report": None,
        "verification": None,
    }
    (tmp_path / "exists.json").write_text(json.dumps({"n": 1}), encoding="utf-8")
    state = {"lines": {}}
    st = ctl.derive_line_state("T-CONFLICT", spec)
    state["lines"]["T-CONFLICT"] = st
    # force a lifecycle UNKNOWN to trigger the conflict surfacer
    st["lifecycle_state"] = "UNKNOWN"
    conflicts = ctl.conflict_scan(state)
    assert conflicts, "expected a conflict to be surfaced"
    c = conflicts[0]
    assert c["state"] == "CONFLICT"
    assert c["resolution"] == "REQUIRED"
    assert c["authority_action"] == "NONE"


# --- Test 4: verdict read from artifact, never invented ---
def test_verdict_read_from_artifact(ctl, tmp_path, monkeypatch):
    monkeypatch.setattr(ctl, "ROOT", tmp_path)
    (tmp_path / "res.json").write_text(json.dumps({"verdict": "SUPPORTED_X"}), encoding="utf-8")
    spec = {
        "prereg": None,
        "runner": None,
        "result_json": "res.json",
        "report": None,
        "verification": None,
    }
    st = ctl.derive_line_state("T-VERDICT", spec)
    assert st["scientific_verdict"] == "SUPPORTED_X"


# --- Test 5: scientific verdict never becomes production authorization ---
def test_verdict_never_production_authorization(ctl):
    # RX-CAPTURE-1 real artifact: CAPTURE_SUPPORTED must stay scientific only.
    st = ctl.derive_line_state("RX-CAPTURE-1", ctl.FULL_STATE["RX-CAPTURE-1"])
    # verdict derived from artifact (candidates) and production impact stays NONE
    assert st["lifecycle_state"] == "CLOSED"
    assert st["verification_state"] in ("VERIFICATION_PASS", "PASS")
    # there is no production_approved field set anywhere by the controller
    assert "production_approved" not in st or not st.get("production_approved")


# --- Test 6: H4 protection (H4D-definition is DEFINITION_LOCKED, not UNKNOWN) ---
def test_h4d_definition_is_definition_locked(ctl):
    st = ctl.derive_line_state("H4D-definition", ctl.FULL_STATE["H4D-definition"])
    assert st["lifecycle_state"] == "CLOSED"
    assert st["scientific_verdict"] == "DEFINITION_LOCKED"
    # and it is definition-only: no result_json expected
    assert ctl.FULL_STATE["H4D-definition"]["result_json"] is None


# --- Test 7: determinism (two runs -> same derived state modulo timestamp) ---
def test_determinism_modulo_timestamp(ctl):
    a = ctl.build_state()
    b = ctl.build_state()
    a.pop("generated_at", None)
    b.pop("generated_at", None)
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)
