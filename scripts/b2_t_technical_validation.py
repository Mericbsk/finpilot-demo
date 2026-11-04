"""Non-blind B2-T artificial arithmetic and metadata-only freeze preparation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

SCOPE = "reports/b2_t_synthetic_technical_validation_SCOPE_DRAFT_v1_2026-10-05.md"
SCOPE_SHA256 = "7f50669db4eed7ce91a529f5015b60946e2933d7d7ab6a3a429c247fd48906e7"
FIXTURES = "reports/b2_t_artificial_fixtures_v1_2026-10-05.json"
SUITE = "tests/test_b2_t_technical_validation_v1.py"
IMPLEMENTATION = "scripts/b2_t_technical_validation.py"
HISTORICAL_COMMIT = "ff9658aa189d8ff0cbb9f3a0fecddab8a50b5b35"


def rational(value: Any) -> Fraction:
    if value is None:
        raise LookupError("missing artificial input")
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise ValueError("finite numeric artificial input required")
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("finite numeric artificial input required") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def round_production(value: Any, digits: int = 4) -> float:
    if isinstance(digits, bool) or digits not in (0, 1, 2, 3, 4):
        raise ValueError("unsupported precision")
    return round(float(rational(value)), digits)


def legacy_producer(atr: Any, known_component: Any) -> float:
    target, component = rational(atr), rational(known_component)
    if target < 0 or not Fraction("-2.5") <= component <= Fraction("7.5"):
        raise ValueError("invalid artificial producer domain")
    normalized = max(0.0, min(1.0, float(target) / 6.0))
    return round((float(component) + 1.5 * normalized) / 10.0 * 100.0, 3)


def v2_producer(gap: Any, rvol: Any, atr: Any, squeeze: Any) -> int:
    factors = [float(rational(value)) for value in (gap, rvol, atr, squeeze)]
    if factors[2] < 0:
        raise ValueError("negative artificial ATR")
    score = (max(0.0, min(1.0, factors[0])) * 30.0
             + max(0.0, min(1.0, factors[1])) * 30.0
             + max(0.0, min(1.0, factors[2] / 4.0)) * 25.0
             + max(0.0, min(1.0, factors[3])) * 15.0)
    return max(0, min(100, round(score)))


def unavailable(status: str, reason: str) -> dict[str, Any]:
    return {"status": status, "decision": "UNRESOLVED", "low": None,
            "high": None, "unbounded_upper": False, "reason": reason}


def interval_result(low: Fraction, high: Fraction | None, threshold: Fraction) -> dict[str, Any]:
    decision = "TRUE" if low >= threshold else "FALSE" if high is not None and high < threshold else "UNRESOLVED"
    return {"status": "VALID_DOMAIN", "decision": decision, "low": str(low),
            "high": str(high) if high is not None else None, "unbounded_upper": high is None}


def atr_interval(stored_score: Any, known_component_low: Any, known_component_high: Any) -> dict[str, Any]:
    if stored_score is None:
        return unavailable("MISSING", "MISSING_STORED_SCORE")
    if known_component_low is None or known_component_high is None:
        return unavailable("UNRESOLVED", "MISSING_COMPONENT_BOUNDS")
    try:
        score = rational(stored_score)
        component_low, component_high = rational(known_component_low), rational(known_component_high)
    except (LookupError, ValueError):
        return unavailable("CONFLICT", "INVALID_NUMERIC_INPUT")
    if not Fraction("-2.5") <= component_low <= component_high <= Fraction("7.5"):
        return unavailable("CONFLICT", "INVALID_COMPONENT_DOMAIN")
    margin = Fraction("0.0005") + Fraction("0.000000001")
    normalized_low = max(Fraction(0), ((score - margin) / 10 - component_high) / Fraction("1.5"))
    normalized_high = min(Fraction(1), ((score + margin) / 10 - component_low) / Fraction("1.5"))
    if normalized_low > normalized_high:
        return unavailable("CONFLICT", "EMPTY_NORMALIZED_DOMAIN")
    scaled_low = normalized_low * 6 * 10000
    lower_units = -(-scaled_low.numerator // scaled_low.denominator)
    low = Fraction(lower_units, 10000)
    if normalized_high == 1:
        return interval_result(low, None, Fraction(4))
    scaled_high = normalized_high * 6 * 10000
    high = Fraction(scaled_high.numerator // scaled_high.denominator, 10000)
    if low > high:
        return unavailable("CONFLICT", "EMPTY_PRODUCTION_PRECISION_GRID")
    return interval_result(low, high, Fraction(4))


def squeeze_producer(short_component: Any, float_component: Any, mode: str) -> float:
    short, floating = rational(short_component), rational(float_component)
    if not 0 <= short <= 1 or not 0 <= floating <= 1 or mode not in {"ON", "OFF"}:
        raise ValueError("invalid artificial squeeze domain")
    short_weight, float_weight = (0.7, 0.3) if mode == "ON" else (0.5, 0.5)
    return round(max(0.0, min(1.0, short_weight * float(short) + float_weight * float(floating))), 4)


def squeeze_interval(stored_on: Any) -> dict[str, Any]:
    if stored_on is None:
        return unavailable("MISSING", "MISSING_STORED_ON")
    try:
        stored = rational(stored_on)
    except (LookupError, ValueError):
        return unavailable("CONFLICT", "INVALID_NUMERIC_INPUT")
    if not 0 <= stored <= 1:
        return unavailable("CONFLICT", "INVALID_STORED_ON_DOMAIN")
    margin = Fraction("0.00005") + Fraction("0.000000001")
    on_low, on_high = max(Fraction(0), stored - margin), min(Fraction(1), stored + margin)
    low = on_low / Fraction("1.4") if on_low <= Fraction("0.7") else Fraction("0.5") + (on_low - Fraction("0.7")) / Fraction("0.6")
    high = on_high / Fraction("0.6") if on_high <= Fraction("0.3") else Fraction("0.5") + (on_high - Fraction("0.3")) / Fraction("1.4")
    return interval_result(max(Fraction(0), low - margin), min(Fraction(1), high + margin), Fraction("0.5"))


def inside_interval(value: Any, result: dict[str, Any]) -> bool:
    if result["status"] != "VALID_DOMAIN":
        return False
    target = rational(value)
    return target >= Fraction(result["low"]) and (result["high"] is None or target <= Fraction(result["high"]))


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    operation, values = case["operation"], case["input"]
    if operation == "round":
        return {"value": round_production(**values)}
    if operation == "legacy":
        return {"value": legacy_producer(**values)}
    if operation == "v2":
        return {"value": v2_producer(**values)}
    if operation == "atr":
        return atr_interval(**values)
    if operation == "squeeze":
        return squeeze_interval(**values)
    if operation == "atr_containment":
        contained = []
        for raw in values["artificial_values"]:
            production = round_production(raw)
            score = legacy_producer(production, values["known_component"])
            result = atr_interval(score, values["known_component"], values["known_component"])
            contained.append(inside_interval(production, result))
        return {"all_contained": all(contained), "checked": len(contained)}
    if operation == "squeeze_containment":
        contained = []
        for components in values["artificial_components"]:
            stored_on = squeeze_producer(**components, mode="ON")
            stored_off = squeeze_producer(**components, mode="OFF")
            contained.append(inside_interval(stored_off, squeeze_interval(stored_on)))
        return {"all_contained": all(contained), "checked": len(contained)}
    if operation == "canonical":
        return {"equal": canonical_json(values["first"]) == canonical_json(values["second"])}
    if operation == "canonical_nonfinite":
        canonical_json({"artificial_nonfinite": float(values["value"])})
        raise RuntimeError("nonfinite payload was not rejected")
    raise ValueError("unsupported artificial operation")


def checked_path(root: Path, relative: str) -> Path:
    member = Path(relative)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError("relative unlinked member required")
    path = root / member
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("member outside declared root")
    for ancestor in (path, *path.parents):
        if ancestor == root:
            break
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError("linked member not allowed")
    return path


def file_identity(path: Path) -> dict[str, Any]:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("member changed during hashing")
    return {"sha256": digest.hexdigest(), "bytes": after.st_size}


def prepare_freeze(root: Path) -> dict[str, Any]:
    if not sys.flags.isolated or not sys.flags.no_site:
        raise ValueError("prepare with python -I -S -B; no site packages or Python environment injection")
    artifacts = [{"id": role, "path": relative, **file_identity(checked_path(root, relative))}
                 for role, relative in (("scope", SCOPE), ("implementation", IMPLEMENTATION), ("fixtures", FIXTURES), ("suite", SUITE))]
    if artifacts[0]["sha256"] != SCOPE_SHA256:
        raise ValueError("approved scope bytes changed")
    fixture = json.loads(checked_path(root, FIXTURES).read_text(encoding="utf-8"))
    expected_ids = [f"T{index:02d}" for index in range(1, 29)]
    if [case["id"] for case in fixture["cases"]] != expected_ids or fixture["contains_historical_rows"]:
        raise ValueError("artificial fixture membership mismatch")
    if fixture["status"] != "FROZEN_EXPECTATIONS_NOT_RUN":
        raise ValueError("fixture status mismatch")
    operations = {"round", "legacy", "v2", "atr", "squeeze", "atr_containment", "squeeze_containment", "canonical", "canonical_nonfinite"}
    for case in fixture["cases"]:
        if case["operation"] not in operations or not case.get("oracle_basis") or not isinstance(case["input"], dict) or not isinstance(case["expected"], dict):
            raise ValueError("unreviewed fixture structure")
    for relative in (IMPLEMENTATION, SUITE):
        ast.parse(checked_path(root, relative).read_text(encoding="utf-8"))
    base = Path(sys.base_prefix).resolve()
    runtime_paths = set()
    for module in tuple(sys.modules.values()):
        for attribute in ("__file__", "__cached__"):
            raw = getattr(module, attribute, None)
            if raw:
                member = Path(raw).resolve()
                if member.is_file() and member.is_relative_to(base):
                    runtime_paths.add(member.relative_to(base).as_posix())
    for name in (f"python{sys.version_info.major}{sys.version_info.minor}.dll", "python3.dll"):
        if (base / name).is_file():
            runtime_paths.add(name)
    runtime = {"implementation": platform.python_implementation(), "version": platform.python_version(),
               "machine": platform.machine(), "executable": file_identity(Path(sys.executable)),
               "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site, "dont_write_bytecode": sys.dont_write_bytecode},
               "third_party_dependencies": [], "stdlib_and_interpreter_members": [{"path": relative, **file_identity(checked_path(base, relative))} for relative in sorted(runtime_paths)],
               "limitations": ["Loaded stdlib source/cache/extensions and Python DLLs hashed, not a full OS DLL or reproducible image snapshot", "Current runtime identity only, not the September historical runtime"]}
    definitions = []
    for relative in ("scanner/score_engine.py", "scanner/features.py"):
        content = subprocess.run(["git", "show", HISTORICAL_COMMIT + ":" + relative], cwd=root, check=True, capture_output=True).stdout
        definitions.append({"path": relative, "commit": HISTORICAL_COMMIT, "sha256": hashlib.sha256(content).hexdigest(), "use": "SOURCE_REFERENCE_ONLY_NOT_IMPORTED_OR_NUMERICAL_INPUT"})
    return {"schema_version": "b2-t-freeze-v1", "study": "B2-T", "scope_sha256": SCOPE_SHA256,
            "status": "PREPARED_FROZEN_NOT_RUN", "execution_authorized": False,
            "authoring": "NON_BLIND_ENGINEERING", "verification": "NOT_INDEPENDENT", "isolation": "NOT_VERIFIED",
            "artifacts": artifacts, "runtime": runtime, "definition_references": definitions,
            "fixture_review": {"reviewer": "GitHub Copilot", "kind": "SELF_REVIEW_ANALYTIC_EXPECTATIONS_NOT_INDEPENDENT", "case_count": len(fixture["cases"]), "numerical_evaluation_performed": False},
            "output_path": "reports/b2_t_technical_results_v1_2026-10-05.json",
            "execution_receipt": None, "limits": ["No real rows, recovery or B2-1 suite execution", "Host authoring context remains visible; -I/-S is not filesystem or network isolation", "No result can satisfy a B2-1 gate", "Explicit separate frozen-bundle execution receipt required"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-freeze", action="store_true", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not args.output.startswith("reports/b2_t_freeze_") or not args.output.endswith(".json"):
        parser.error("new reports/b2_t_freeze_*.json output required")
    output = checked_path(root, args.output)
    if output.exists():
        parser.error("refusing to overwrite a frozen artifact")
    payload = canonical_json(prepare_freeze(root))
    with output.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(payload)
    print(canonical_json({"output": args.output, "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(), "status": "PREPARED_FROZEN_NOT_RUN"}), end="")


if __name__ == "__main__":
    main()
