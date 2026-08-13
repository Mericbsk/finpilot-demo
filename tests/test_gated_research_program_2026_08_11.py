from pathlib import Path

from research.gated_research_program_2026_08_11 import evaluate_gates, program_manifest


def test_manifest_has_220_pre_registered_tests_and_25_priority_tests():
    manifest = program_manifest()

    assert manifest["planned_test_count"] == 220
    assert manifest["priority_test_count"] == 25
    assert manifest["production_change"] is False
    assert len(manifest["phases"]) == 10


def test_blocked_prerequisite_keeps_later_phases_closed(tmp_path: Path):
    source = tmp_path / "export.csv"
    source.write_text("symbol,scan_date\nAAA,2026-01-01\n", encoding="utf-8")

    result = evaluate_gates(source_csv=source)

    assert result["phase_status"]["P0"] == "COMPLETED"
    assert result["phase_status"]["P1"] == "BLOCKED"
    assert result["phase_status"]["P2"] == "BLOCKED"
    assert result["phase_status"]["P3"] == "NOT_OPENED"
    assert result["phase_status"]["P9"] == "BLOCKED"
    assert result["locked_oos"] == "NOT_OPENED"
    assert result["production_boundary"] == "UNCHANGED"
