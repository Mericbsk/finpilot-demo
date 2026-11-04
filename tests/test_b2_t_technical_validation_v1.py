"""Opt-in B2-T suite; no tests execute or collect without an exact freeze receipt."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any


def safe_path(root: Path, relative: str) -> Path:
    member = Path(relative)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError("relative unlinked input required")
    path = root / member
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("input outside declared root")
    for ancestor in (path, *path.parents):
        if ancestor == root:
            break
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError("linked input not allowed")
    return path


def digest(path: Path) -> str:
    before = path.stat()
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("input changed while hashing")
    return result.hexdigest()


def run_case(module: Any, case: dict[str, Any]) -> dict[str, Any]:
    try:
        observed = module.evaluate_case(case)
    except (ValueError, LookupError, RuntimeError, TypeError) as exc:
        observed = {"exception": type(exc).__name__}
    passed = all(key in observed and observed[key] == value for key, value in case["expected"].items())
    return {"id": case["id"], "status": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "observed": observed, "expected": case["expected"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--execution-receipt", required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        parser.error("run with python -I -S -B; these flags are not filesystem/network isolation")
    root = Path(__file__).resolve().parents[1]
    manifest_path, receipt_path = safe_path(root, args.manifest), safe_path(root, args.execution_receipt)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    freeze_sha = digest(manifest_path)
    if receipt.get("study") != "B2-T" or receipt.get("execution_authorized") is not True or receipt.get("approved_by") != "Meric" or receipt.get("freeze_sha256") != freeze_sha:
        parser.error("exact-bundle human execution receipt missing or mismatched")
    if manifest["study"] != "B2-T" or manifest["status"] != "PREPARED_FROZEN_NOT_RUN" or manifest["execution_authorized"]:
        parser.error("unexpected preparation freeze identity/state")
    permitted = {"scope": "reports/b2_t_synthetic_technical_validation_SCOPE_DRAFT_v1_2026-10-05.md", "implementation": "scripts/b2_t_technical_validation.py", "fixtures": "reports/b2_t_artificial_fixtures_v1_2026-10-05.json", "suite": "tests/test_b2_t_technical_validation_v1.py"}
    if len(manifest["artifacts"]) != len(permitted) or {item["id"]: item["path"] for item in manifest["artifacts"]} != permitted:
        parser.error("unexpected member-level inputs")
    for artifact in manifest["artifacts"]:
        if digest(safe_path(root, artifact["path"])) != artifact["sha256"]:
            parser.error("frozen artifact mismatch")
    runtime = manifest["runtime"]
    if runtime["version"] != platform.python_version() or runtime["implementation"] != platform.python_implementation() or runtime["machine"] != platform.machine() or runtime["executable"]["sha256"] != digest(Path(sys.executable)):
        parser.error("current runtime identity mismatch")
    for artifact in runtime["stdlib_and_interpreter_members"]:
        if digest(safe_path(Path(sys.base_prefix).resolve(), artifact["path"])) != artifact["sha256"]:
            parser.error("runtime member mismatch")
    output = safe_path(root, "reports/b2_t_technical_results_v1_2026-10-05.json")
    if manifest["output_path"] != output.relative_to(root).as_posix() or output.exists():
        parser.error("refusing undeclared output or result overwrite")
    spec = importlib.util.spec_from_file_location("b2_t_frozen_implementation", safe_path(root, permitted["implementation"]))
    if spec is None or spec.loader is None:
        raise RuntimeError("frozen technical implementation unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = json.loads(safe_path(root, permitted["fixtures"]).read_text(encoding="utf-8"))
    outcomes = []
    for case in fixture["cases"]:
        outcome = run_case(module, case)
        outcomes.append(outcome)
        if outcome["status"] != "TECHNICAL_PASS":
            break
    status = "TECHNICAL_PASS" if len(outcomes) == len(fixture["cases"]) and all(item["status"] == "TECHNICAL_PASS" for item in outcomes) else "TECHNICAL_FAIL"
    result = {"study": "B2-T", "freeze_sha256": freeze_sha, "execution_receipt_sha256": digest(receipt_path), "status": status, "cases": outcomes,
              "not_run_case_ids": [case["id"] for case in fixture["cases"][len(outcomes):]],
              "authoring": "NON_BLIND_ENGINEERING", "verification": "NOT_INDEPENDENT", "isolation": "NOT_VERIFIED",
              "limitations": ["Non-blind technical checks only; no historical recovery or B2-1 gate acceptance", "Receipt fields require custodial human-approval evidence; not cryptographic authentication", "No OS-level filesystem/network sandbox is certified"]}
    payload = module.canonical_json(result)
    with output.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(payload)
    print(module.canonical_json({"output": output.relative_to(root).as_posix(), "status": status, "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest()}), end="")
    if status != "TECHNICAL_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
