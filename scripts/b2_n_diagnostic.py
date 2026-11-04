"""Separate non-blind conditional diagnostics; never the B2-1 runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import runpy
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

SCOPE = "reports/b2_n_diagnostic_scope_v1_2026-10-06.md"
RUNNER = "scripts/b2_n_diagnostic.py"
TESTS = "tests/test_b2_n_diagnostic.py"
MODEL = "scripts/b2_t_technical_validation.py"
SUITE = "tests/test_b2_t_technical_validation_v1.py"
FIXTURES = "reports/b2_t_artificial_fixtures_v1_2026-10-05.json"
INPUT = "reports/b2_1_staged_candidate_v1_2026-10-06/historical_scan_export.json"
OUTPUT = "reports/b2_n_diagnostic_results_v1_2026-10-06.json"


def identity(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_path(root: Path, relative: str) -> Path:
    member = Path(relative)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError("relative member required")
    path = root / member
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("member escape")
    for ancestor in (path, *path.parents):
        if ancestor == root:
            break
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError("linked member")
    return path


def numeric_factor(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and 0 <= value <= 1 and math.isfinite(value)


def diagnose_rows(rows: list[dict[str, Any]], model: Any) -> list[dict[str, Any]]:
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("all original rows must be objects")
    results = []
    for index, row in enumerate(rows):
        state = "MISSING" if "entry_ok" not in row else "TRUE" if row["entry_ok"] is True else "FALSE" if row["entry_ok"] is False else "MALFORMED"
        record = {"row_index": index, "symbol": row.get("symbol"), "entry_ok_state": state,
                  "historical_identity": "UNKNOWN", "historical_recovery_claim": "NOT_ESTABLISHED",
                  "atr": {"status": "NOT_EVALUATED", "reason": "COMPONENT_PRECISION_NOT_ESTABLISHED"}}
        factor = row.get("squeeze_factor")
        nested = row.get("score_input")
        reason = None
        if state != "TRUE":
            reason = "OUTSIDE_NUMERICAL_SCOPE" if state == "FALSE" else "UNKNOWN_ELIGIBILITY"
        elif factor is None:
            reason = "MISSING_TOP_LEVEL_SQUEEZE"
        elif not numeric_factor(factor):
            reason = "INVALID_TOP_LEVEL_SQUEEZE"
        elif isinstance(nested, dict) and "squeeze_factor" in nested and (not numeric_factor(nested["squeeze_factor"]) or nested["squeeze_factor"] != factor):
            reason = "NESTED_ENCODING_DISAGREEMENT"
        if reason:
            record["squeeze"] = {"status": "NOT_EVALUATED", "reason": reason}
        else:
            record["squeeze"] = {"status": "CONDITIONAL_MODEL_ONLY", "assumption": "STORED_FIELD_IS_ON_MODEL_OUTPUT_NOT_VERIFIED",
                                 "model_result": model.squeeze_interval(factor)}
        results.append(record)
    return results


def load_module(path: Path, name: str) -> Any:
    return SimpleNamespace(**runpy.run_path(str(path), run_name=name))


def prepare_freeze(root: Path) -> dict[str, Any]:
    frozen = {MODEL: "0c3202ca1bea5b7bebb380bc6134a112dc7c233ac0ee0304cdc5fc3368f6b350",
              SUITE: "53db1a512550e3c524d2485105474d19dfee7852ef8caedabb1605003e00ca94",
              FIXTURES: "b6cdcce0a4c19ea50b4a4066f9fd8914df64da8a3767a9fb771463c64f138f39",
              INPUT: "0d67abf98ef8c9a5f94db201f671529917cea3e2677344ae3d582e3fb1406a49"}
    artifacts = [{"path": relative, "sha256": identity(checked_path(root, relative))}
                 for relative in (SCOPE, RUNNER, TESTS, MODEL, SUITE, FIXTURES, INPUT)]
    if any(item["path"] in frozen and item["sha256"] != frozen[item["path"]] for item in artifacts):
        raise ValueError("previously frozen source mismatch")
    load_module(checked_path(root, MODEL), "b2_n_metadata_model")
    load_module(checked_path(root, SUITE), "b2_n_metadata_suite")
    base = Path(sys.base_prefix).resolve()
    members = set()
    for module in tuple(sys.modules.values()):
        for attribute in ("__file__", "__cached__"):
            raw = getattr(module, attribute, None)
            if raw:
                path = Path(raw).resolve()
                if path.is_file() and path.is_relative_to(base):
                    members.add(path.relative_to(base).as_posix())
    for name in (f"python{sys.version_info.major}{sys.version_info.minor}.dll", "python3.dll"):
        if (base / name).is_file():
            members.add(name)
    return {"study": "B2-N", "version": 1, "status": "FROZEN_NOT_RUN", "output": OUTPUT,
            "artifacts": artifacts, "authoring": "NON_BLIND_ENGINEERING", "verification": "NOT_INDEPENDENT",
            "blindness": "NOT_VERIFIED", "execution_authorized": False,
            "runtime": {"version": sys.version, "executable_sha256": identity(Path(sys.executable)),
                        "members": [{"path": relative, "sha256": identity(checked_path(base, relative))} for relative in sorted(members)],
                        "scope": "CURRENT_INTERPRETER_LOADED_STDLIB_NOT_HISTORICAL_RUNTIME_OR_OS_SANDBOX"}}


def validate_receipt(receipt: dict[str, Any], manifest_sha256: str) -> None:
    if receipt.get("study") != "B2-N" or receipt.get("approved_by") != "Meric" or receipt.get("execution_authorized") is not True or receipt.get("manifest_sha256") != manifest_sha256:
        raise ValueError("exact B2-N receipt required")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--receipt")
    parser.add_argument("--prepare-freeze", action="store_true")
    args = parser.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError("python -I -S -B required")
    root = Path(__file__).resolve().parents[1]
    manifest_path = checked_path(root, args.manifest)
    if args.prepare_freeze:
        if not args.manifest.startswith("reports/b2_n_freeze_") or manifest_path.exists():
            raise ValueError("new B2-N freeze path required")
        payload = prepare_freeze(root)
        with manifest_path.open("x", encoding="ascii", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
        print(json.dumps({"manifest": args.manifest, "sha256": identity(manifest_path), "real_arithmetic": "NOT_RUN"}))
        return
    if not args.receipt:
        parser.error("--receipt required for execution")
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    receipt = json.loads(checked_path(root, args.receipt).read_text(encoding="ascii"))
    validate_receipt(receipt, identity(manifest_path))
    expected = {SCOPE, RUNNER, TESTS, MODEL, SUITE, FIXTURES, INPUT}
    if manifest.get("study") != "B2-N" or manifest.get("output") != OUTPUT or {item["path"] for item in manifest["artifacts"]} != expected or len(manifest["artifacts"]) != len(expected):
        raise ValueError("fixed artifact binding required")
    output = checked_path(root, OUTPUT)
    if output.exists():
        raise ValueError("refusing output overwrite")

    def verify() -> None:
        for item in manifest["artifacts"]:
            if identity(checked_path(root, item["path"])) != item["sha256"]:
                raise ValueError("artifact integrity mismatch")
        if identity(Path(sys.executable)) != manifest["runtime"]["executable_sha256"]:
            raise ValueError("runtime executable mismatch")
        for item in manifest["runtime"]["members"]:
            if identity(checked_path(Path(sys.base_prefix).resolve(), item["path"])) != item["sha256"]:
                raise ValueError("runtime member mismatch")

    verify()
    model = load_module(checked_path(root, MODEL), "b2_n_frozen_model")
    suite = load_module(checked_path(root, SUITE), "b2_n_reused_technical_suite")
    fixtures = json.loads(checked_path(root, FIXTURES).read_text(encoding="ascii"))
    if [case["id"] for case in fixtures["cases"]] != [f"T{index:02d}" for index in range(1, 29)]:
        raise ValueError("frozen self-check membership mismatch")
    checks = []
    for case in fixtures["cases"]:
        outcome = suite.run_case(model, case)
        if outcome["status"] != "TECHNICAL_PASS":
            raise ValueError("reused artificial self-check failure; STOP")
        checks.append(outcome)
    doc = json.loads(checked_path(root, INPUT).read_text(encoding="ascii"))
    rows = diagnose_rows(doc["results"], model)
    payload = {"study": "B2-N", "status": "COMPLETED_CONDITIONAL_DIAGNOSTIC", "authoring": "NON_BLIND_ENGINEERING",
               "verification": "NOT_INDEPENDENT", "blindness": "NOT_VERIFIED", "b2_1_lock": "BLOCKED",
               "b2_1_scientific_execution": "NOT_RUN", "manifest_sha256": identity(manifest_path),
               "receipt_sha256": identity(checked_path(root, args.receipt)), "reused_artificial_checks_passed": len(checks),
               "row_count": len(rows), "eligibility_counts": dict(Counter(row["entry_ok_state"] for row in rows)),
               "squeeze_status_counts": dict(Counter(row["squeeze"]["status"] for row in rows)),
               "conditional_decision_counts": dict(Counter(row["squeeze"]["model_result"]["decision"] for row in rows if row["squeeze"]["status"] == "CONDITIONAL_MODEL_ONLY")),
               "limitations": ["Actual historical ON mode and production linkage/precision unverified", "Conditional model outputs are not historical recovery or independent verification", "ATR, R1, R3, R5, risk and performance not evaluated", "No B2-1 synthetic gate or scientific acceptance", "Python startup restrictions are not OS isolation"],
               "rows": rows}
    verify()
    with output.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(model.canonical_json(payload))
    print(json.dumps({"study": "B2-N", "output": OUTPUT, "sha256": identity(output), "row_count": len(rows), "conditional_decision_counts": payload["conditional_decision_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
