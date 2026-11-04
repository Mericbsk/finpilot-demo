"""Non-blind custodian metadata helpers; never a recovery runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HISTORICAL_COMMIT = "ff9658aa189d8ff0cbb9f3a0fecddab8a50b5b35"
PROTOCOL = "reports/b2_1_provenance_recovery_preregistration_DRAFT_v3_2026-10-05.md"
APPROVED_PROTOCOL_SHA256 = "6745641a28a254f2ff1c8d2fb6dc2ec599b58d7685248b73a361ef46ac2feaf0"
FIXTURES = "reports/b2_1_synthetic_fixtures_candidate_v3_2026-10-05.json"
BASE_MANIFEST = "reports/b2_1_prelock_manifest_candidate_v1_2026-10-05.json"
BASE_MANIFEST_SHA256 = "84c7879c1231aa17647a97ed818469d71a44cb919397ee6db19e6ebb705f76bb"
CLOSURE_AUDIT = "reports/b2_1_prelock_closure_audit_v1_2026-10-05.json"
CLOSURE_AUDIT_SHA256 = "829700b264a83e4a90952374fa5a7c6c1d085ebca159e6ebb2983c152249368c"


def checked_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("artifact path must stay inside the workspace")
    base = root.resolve()
    path = base / candidate
    for ancestor in (path, *path.parents):
        if ancestor == base:
            break
        if ancestor.is_symlink() or ancestor.is_junction():
            raise ValueError("linked artifacts are not permitted")
    if not path.resolve().is_relative_to(base):
        raise ValueError("artifact path escapes the workspace")
    return path


def artifact_record(root: Path, relative: str) -> dict[str, Any]:
    path = checked_path(root, relative)
    if not path.is_file():
        return {"path": relative, "availability": "NOT_FOUND", "sha256": None}
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("artifact changed during hashing")
    return {
        "path": relative,
        "availability": "AVAILABLE",
        "sha256": digest.hexdigest(),
        "bytes": after.st_size,
        "filesystem_mtime_utc": datetime.fromtimestamp(after.st_mtime, UTC).isoformat(),
        "source_timestamp": None,
        "historical_identity": "UNKNOWN",
        "temporal_validity": "UNKNOWN",
        "mtime_is_provenance": False,
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def git_bytes(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True
    ).stdout


def git_blob_sha256(root: Path, object_id: str) -> str:
    digest = hashlib.sha256()
    with subprocess.Popen(["git", "cat-file", "blob", object_id], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        if process.stdout is None:
            raise RuntimeError("git object stream unavailable")
        for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
            digest.update(chunk)
        if process.wait() != 0:
            raise RuntimeError("historical blob read failed")
    return digest.hexdigest()


def code_record(path: str, content: bytes) -> dict[str, Any]:
    tree = ast.parse(content)
    functions = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        calls = sorted({ast.unparse(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)})
        rounds = sorted({
            ast.unparse(call) for call in ast.walk(node)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "round"
        })
        functions.append({"symbol": node.name, "line": node.lineno, "calls": calls, "round_expressions": rounds})
    return {
        "path": path, "commit": HISTORICAL_COMMIT,
        "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
        "role": "code_definition", "symbols": functions,
        "definition_evidence": "STATIC_AST_NOT_IMPORTED",
        "call_path_status": "LOCAL_CALL_REFERENCES_ONLY_DEPENDENCY_CLOSURE_NOT_VERIFIED",
        "runtime_precision_identity": "UNKNOWN",
    }


def static_import_evidence(path: str, content: bytes, available_paths: set[str]) -> dict[str, Any]:
    tree = ast.parse(content)
    imports = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue
        invalid_relative = False
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        else:
            package = path.split("/")[:-1]
            if node.level:
                keep = len(package) - node.level + 1
                invalid_relative = not package or keep < 0
                prefix = package[:max(keep, 0)]
            else:
                prefix = []
            components = prefix + (node.module.split(".") if node.module else [])
            base = ".".join(components)
            modules = [base] if base else []
            modules.extend(".".join(components + [alias.name]) for alias in node.names if alias.name != "*")
        targets = set()
        if not invalid_relative:
            for module in modules:
                components = module.split(".")
                for depth in range(1, len(components) + 1):
                    relative = "/".join(components[:depth])
                    targets.update(candidate for candidate in (relative + ".py", relative + "/__init__.py") if candidate in available_paths)
        imports.append({
            "line": node.lineno, "statement": ast.unparse(node), "local_candidates": sorted(targets),
            "resolution": "INVALID_RELATIVE_REFERENCE" if invalid_relative else "LOCAL_STATIC_CANDIDATES" if targets else "EXTERNAL_OR_UNRESOLVED",
            "runtime_resolution_verified": False,
        })
    dynamic = [{"line": node.lineno, "call": ast.unparse(node.func)} for node in ast.walk(tree)
               if isinstance(node, ast.Call) and (isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}
               or isinstance(node.func, ast.Attribute) and node.func.attr in {"import_module", "exec_module", "load_module"})]
    return {"imports": sorted(imports, key=lambda record: record["line"]), "dynamic_loading_review": dynamic,
            "scope": "SYNTAX_REFERENCES_ALL_BRANCHES_NOT_RUNTIME_OR_SYMBOL_CLOSURE"}


def prepare_definition_closure(root: Path) -> dict[str, Any]:
    if artifact_record(root, PROTOCOL)["sha256"] != APPROVED_PROTOCOL_SHA256 or artifact_record(root, BASE_MANIFEST)["sha256"] != BASE_MANIFEST_SHA256:
        raise ValueError("frozen definition authority mismatch")
    if git_bytes(root, "rev-parse", HISTORICAL_COMMIT + "^{commit}").decode().strip() != HISTORICAL_COMMIT:
        raise ValueError("historical commit identity mismatch")
    base = json.loads(checked_path(root, BASE_MANIFEST).read_text(encoding="utf-8"))
    expected = {record["path"]: record["sha256"] for record in base["historical_code_definitions"]}
    available = {path for path in git_bytes(root, "ls-tree", "-r", "--name-only", HISTORICAL_COMMIT).decode().splitlines() if path.endswith(".py")}
    pending = set(expected)
    members = {}
    while pending:
        path = min(pending)
        pending.remove(path)
        if path in members:
            continue
        content = git_bytes(root, "show", HISTORICAL_COMMIT + ":" + path)
        digest = hashlib.sha256(content).hexdigest()
        if path in expected and digest != expected[path]:
            raise ValueError("frozen definition member mismatch")
        try:
            record = code_record(path, content)
            record["static_dependencies"] = static_import_evidence(path, content, available)
        except SyntaxError as error:
            record = {"path": path, "sha256": digest, "commit": HISTORICAL_COMMIT,
                      "parse_status": "SYNTAX_BLOCKED", "parse_error_line": error.lineno,
                      "static_dependencies": {"imports": [], "dynamic_loading_review": [], "scope": "NOT_PARSED"}}
        record["seed_member"] = path in expected
        record["blind_bundle_allowed"] = False
        members[path] = record
        pending.update(target for item in record["static_dependencies"]["imports"] for target in item["local_candidates"] if target not in members)
    return {
        "schema_version": "b2-1-static-definition-closure-candidate-v1", "layer": "Research", "level": "A",
        "role": "NON_BLIND_CUSTODIAN", "protocol_sha256": APPROVED_PROTOCOL_SHA256,
        "baseline_sha256": BASE_MANIFEST_SHA256, "historical_commit_full": HISTORICAL_COMMIT,
        "seed_members": sorted(expected), "members": [members[path] for path in sorted(members)],
        "static_reference_traversal_completed": True, "full_dependency_precision_review": "PENDING",
        "historical_execution_identity": "UNKNOWN", "historical_runtime_identity": "UNKNOWN",
        "locked": False, "execution_authorized": False, "real_execution_performed": False, "synthetic_gate": "NOT_RUN",
        "limitations": ["Static references across all branches are a conservative candidate graph, not an executed call graph", "Local file presence does not prove runtime import resolution or exported-symbol precision", "Dynamic loading, third-party implementations, config, providers, overrides and actual runtime require separate evidence", "Syntax-blocked members prevent a full closure claim", "No modules imported; no real values compared; no final member authorization"],
    }


def export_schema(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = doc["results"]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("historical population must be an unfiltered list of object rows")
    allowed = {"symbol", "entry_ok", "score_input", "legacy_quality_score", "v2_score", "squeeze_factor", "conviction_tier", "feature_timestamps", "scan_id"}
    return {
        "observed_date": doc.get("date"), "declared_result_count": doc.get("result_count"),
        "population_count": len(rows), "population_filtered": False,
        "scan_complete": doc.get("scan_complete"), "source_timestamp": doc.get("generated_at"),
        "top_level_identity_fields_present": [name for name in ("scan_id", "run_id") if name in doc],
        "allowed_row_fields_present": sorted(allowed.intersection({key for row in rows for key in row})),
        "score_input_schema": sorted({key for row in rows if isinstance(row.get("score_input"), dict) for key in row["score_input"]}),
        "row_to_scan_identity_mapping": "REQUIRES_REVIEW_TOP_LEVEL_IDENTITY_NOT_ROW_FIELD",
        "eligibility": "NOT_EVALUATED", "recovery_values_compared": False,
    }


def population_identity(doc: dict[str, Any]) -> dict[str, Any]:
    rows = doc["results"]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("population must preserve every object row")
    states = {"TRUE": 0, "FALSE": 0, "MISSING": 0, "MALFORMED": 0}
    members = []
    symbols: dict[str, int] = {}
    invalid_symbols = 0
    for index, row in enumerate(rows):
        if "entry_ok" not in row:
            state = "MISSING"
        elif row["entry_ok"] is True:
            state = "TRUE"
        elif row["entry_ok"] is False:
            state = "FALSE"
        else:
            state = "MALFORMED"
        states[state] += 1
        symbol = row.get("symbol")
        valid = isinstance(symbol, str) and bool(symbol) and symbol == symbol.strip()
        if valid:
            symbols[symbol] = symbols.get(symbol, 0) + 1
        else:
            invalid_symbols += 1
        members.append({"row_index": index, "symbol": symbol if valid else None, "entry_ok_state": state})
    return {
        "row_count": len(rows), "unique_valid_symbols": len(symbols),
        "duplicate_symbol_counts": {symbol: count for symbol, count in sorted(symbols.items()) if count > 1},
        "missing_or_malformed_symbol_rows": invalid_symbols,
        "entry_ok_states": states, "entry_ok_is_complete": not (states["MISSING"] or states["MALFORMED"]),
        "population_rule": "EVERY_RESULT_ROW_IN_ORIGINAL_ORDER_NO_FILTER_NO_DEDUPLICATION",
        "population_membership_sha256": hashlib.sha256(canonical_json(members).encode("ascii")).hexdigest(),
        "membership_hash_scope": "row_index, exact valid symbol, observed entry_ok state; not recovery values",
        "target_eligibility_review": "PENDING_PROTOCOL_TARGET_MAPPING",
        "historical_execution_identity": "UNKNOWN",
    }


def project_export(doc: dict[str, Any], allowed_fields: list[str]) -> dict[str, Any]:
    before = population_identity(doc)
    if not allowed_fields or any(not isinstance(field, str) for field in allowed_fields) or len(set(allowed_fields)) != len(allowed_fields):
        raise ValueError("explicit unique field allowlist required")
    staged = {"results": [{key: row[key] for key in allowed_fields if key in row} for row in doc["results"]]}
    after = population_identity(staged)
    if before["population_membership_sha256"] != after["population_membership_sha256"]:
        raise ValueError("projection changes population identity or eligibility")
    return staged


def prepare_staged_export(root: Path) -> dict[str, Any]:
    if artifact_record(root, PROTOCOL)["sha256"] != APPROVED_PROTOCOL_SHA256 or artifact_record(root, BASE_MANIFEST)["sha256"] != BASE_MANIFEST_SHA256:
        raise ValueError("frozen staging authority mismatch")
    protocol = checked_path(root, PROTOCOL).read_text(encoding="utf-8")
    blocks = re.findall(r"```json\s*\n(.*?)\n```", protocol, re.DOTALL)
    if len(blocks) != 1:
        raise ValueError("single authoritative manifest template required")
    template = json.loads(blocks[0])
    definitions = [record for record in template["artifacts"] if record["id"] == "historical_scan_export"]
    if len(definitions) != 1:
        raise ValueError("single historical export definition required")
    allowed = definitions[0]["allowed_fields"]
    base = json.loads(checked_path(root, BASE_MANIFEST).read_text(encoding="utf-8"))
    relative = "data/distribution/scan_export_2026-09-09.json"
    source = artifact_record(root, relative)
    expected = next(record["sha256"] for record in base["historical_scan_export_candidates"] if record["path"] == relative)
    if source["sha256"] != expected:
        raise ValueError("source export differs from frozen candidate")
    doc = json.loads(checked_path(root, relative).read_text(encoding="utf-8-sig"))
    staged = project_export(doc, allowed)
    payload = canonical_json(staged)
    if artifact_record(root, relative)["sha256"] != expected:
        raise RuntimeError("source export changed during projection")
    stage_relative = "reports/b2_1_staged_candidate_v1_2026-10-06/historical_scan_export.json"
    path = checked_path(root, stage_relative)
    if path.exists():
        raise ValueError("refusing to overwrite staged candidate")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(payload)
    stage = artifact_record(root, stage_relative)
    if stage["sha256"] != hashlib.sha256(payload.encode("ascii")).hexdigest():
        raise RuntimeError("staged candidate hash mismatch")
    return {
        "schema_version": "b2-1-staged-export-candidate-v1", "layer": "Research", "level": "A",
        "role": "NON_BLIND_CUSTODIAN", "status": "CANDIDATE_ONLY_LOCK_BLOCKED",
        "protocol": {"path": PROTOCOL, "sha256": APPROVED_PROTOCOL_SHA256},
        "source": source, "staged_member": stage, "allowed_row_fields": allowed,
        "source_envelope_fields_not_staged": sorted(key for key in doc if key != "results"),
        "population": population_identity(staged), "projection": "FIELD_PROJECTION_NO_FILTER_NO_DEDUPLICATION_NO_IMPUTATION",
        "final_allowlist_status": "PENDING_MEMBER_AND_LINEAGE_REVIEW", "blind_bundle_allowed": False,
        "locked": False, "execution_authorized": False, "synthetic_gate": "NOT_RUN",
        "real_execution_performed": False, "historical_execution_identity": "UNKNOWN",
        "limitations": ["Field names come from unchanged approved V3, not a new rule", "Top-level identity/envelope stays in source; final lineage mapping remains required", "Nested allowed fields are retained without value comparison; nested definitions and temporal evidence still require review", "This is one staged export candidate, not a finalized manifest or blind bundle", "No source requiredness or inventory gate is closed by staging this member"],
    }


def disposition(record: dict[str, Any], seen: dict[str, str]) -> dict[str, Any]:
    path = record["path"]
    digest = record.get("sha256")
    classification = "UNRESOLVED"
    reason = "Path family alone does not establish historical definition, timing or use."
    duplicate_of = None
    excluded = record.get("role") == "RESEARCH_RESULT_EXCLUDED_FROM_BLIND_BUNDLE" or bool(re.search(
        r"(?:ab_results|ab_stats|combined_results|combined_summary|experiments_results|optuna|walkforward|wf_mc|component_ablation|component_correlation|offline_ablation)", path
    ))
    if digest and digest in seen:
        classification = "DUPLICATE_REFERENCE"
        duplicate_of = seen[digest]
        reason = "Identical bytes in frozen snapshot; retain reference, do not deduplicate population."
    elif excluded:
        classification = "RESEARCH_RESULT_EXCLUDED"
        reason = "Existing excluded role or research-result filename family; contents not parsed."
    elif path.startswith(("data/price_cache/", "data/daily_cache_h/", "data/intraday_cache/", "data/finra_cache/", "data/news_cache/", "data/edgar_cache/")) or path == "data/fundamentals_cache.json":
        classification = "EXTERNAL_CANDIDATE"
        reason = "Cache/source candidate by path only; provider/units/PIT/identity unestablished."
    elif re.search(r"(?:dictionary|onboarding|waitlist|watchlist|finsense_cases)", path):
        classification = "OUT_OF_SCOPE"
        reason = "Content/user workflow file family outside declared B2-1 inputs; no contents inspected."
    if digest and digest not in seen:
        seen[digest] = path
    return {
        "path": path, "snapshot_sha256": digest,
        "evidence_classification": classification,
        "classification_basis": "FROZEN_METADATA_AND_PATH_FAMILY_NOT_CONTENT_PROVENANCE",
        "reason": reason, "duplicate_of": duplicate_of,
        "final_allowlist_status": "EXCLUDED_BY_PROTOCOL" if excluded else "PENDING_HUMAN_REVIEW",
        "blind_bundle_allowed": False,
    }


def archive_date_hits(root: Path) -> dict[str, Any]:
    records = []
    unavailable_roots = []
    for relative_root in ("logs", "data/logs", "data/distribution"):
        directory = checked_path(root, relative_root)
        if not directory.is_dir():
            unavailable_roots.append(relative_root)
            continue
        for path in sorted(directory.rglob("*")):
            if path.suffix.lower() not in {".log", ".jsonl"} or not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if any(token in relative.lower() for token in ("secret", "credential", "token", "session", "user", "auth")):
                continue
            record = artifact_record(root, relative)
            matches = []
            with path.open(encoding="utf-8", errors="replace") as handle:
                for index, line in enumerate(handle, 1):
                    if "2026-09-09" in line and re.search(r"scan|publish|publication|export|scheduler", line, re.IGNORECASE):
                        matches.append({"line": index, "date_text_match": True,
                                        "identity_key_markers": sorted({key for key in ("scan_id", "run_id", "commit", "git_sha", "config_sha") if key in line})})
            if artifact_record(root, relative)["sha256"] != record["sha256"]:
                raise RuntimeError("archive changed during metadata search")
            records.append({"path": relative, "sha256": record["sha256"], "date_matches": matches})
    return {
        "scope": "Current .log/.jsonl files under logs, data/logs, data/distribution; exact text date 2026-09-09 plus event keyword.",
        "files": records, "unavailable_roots": unavailable_roots,
        "limitations": ["No secrets or full log messages emitted", "date/keyword matches are leads, not execution identity", "JSON snapshots, rotated/compressed archives, database and external CI/deployment records not searched by this routine", "No scan/publication identity or historical flags inferred from text match"],
        "historical_execution_identity": "UNKNOWN",
    }


def prepare_closure_audit(root: Path) -> dict[str, Any]:
    base = artifact_record(root, BASE_MANIFEST)
    if base["sha256"] != BASE_MANIFEST_SHA256 or artifact_record(root, PROTOCOL)["sha256"] != APPROVED_PROTOCOL_SHA256:
        raise ValueError("frozen preparation authority mismatch")
    manifest = json.loads(checked_path(root, BASE_MANIFEST).read_text(encoding="utf-8"))
    export_path = "data/distribution/scan_export_2026-09-09.json"
    export = artifact_record(root, export_path)
    expected_export = next(record["sha256"] for record in manifest["historical_scan_export_candidates"] if record["path"] == export_path)
    if export["sha256"] != expected_export:
        raise ValueError("historical export changed since preparation")
    population = population_identity(json.loads(checked_path(root, export_path).read_text(encoding="utf-8-sig")))
    if artifact_record(root, export_path)["sha256"] != export["sha256"]:
        raise RuntimeError("export changed during population inspection")
    seen: dict[str, str] = {}
    records = [disposition(record, seen) for record in manifest["raw_cache_inventory"]]
    paths = ["scanner/features.py", "scanner/evaluate.py", "scanner/score_engine.py", "scanner/risk_engine.py", "scanner/execution_policy.py", "scanner/scan_summary.py", "scanner/position_sizer.py", "api/routers/scan.py", "distribution/snapshot_builder.py", "distribution/schema.py", "distribution/jobs.py"]
    definitions = [code_record(path, git_bytes(root, "show", HISTORICAL_COMMIT + ":" + path)) for path in paths]
    constraints = []
    historical_paths = git_bytes(root, "ls-tree", "-r", "--name-only", HISTORICAL_COMMIT).decode().splitlines()
    for path in historical_paths:
        if Path(path).name in {"Dockerfile", "requirements.txt", "pyproject.toml", "docker-compose.yml", "requirements.lock", "poetry.lock", "uv.lock", "Pipfile.lock"}:
            content = git_bytes(root, "show", HISTORICAL_COMMIT + ":" + path)
            constraints.append({"path": path, "sha256": hashlib.sha256(content).hexdigest(), "evidence_strength": "SOURCE_CONSTRAINT_NOT_INSTALLED_RUNTIME_IDENTITY"})
    runtime_history = git_bytes(root, "log", manifest["observed_head"], "--format=%H", "--name-only", "--", "*requirements*lock*", "*poetry.lock", "*uv.lock", "*Pipfile.lock", "*environment*.yml", "*deployment*.yaml").decode().splitlines()
    return {
        "schema_version": "b2-1-closure-evidence-audit-v1", "layer": "Research", "level": "A",
        "role": "NON_BLIND_CUSTODIAN", "status": "LOCK_BLOCKED",
        "locked": False, "execution_authorized": False, "synthetic_gate": "NOT_RUN",
        "blind_execution": {"status": "NOT_VERIFIED"}, "real_execution_performed": False,
        "protocol": {"path": PROTOCOL, "approved_sha256": APPROVED_PROTOCOL_SHA256},
        "baseline_manifest": base, "historical_commit": HISTORICAL_COMMIT,
        "export_candidate": export, "population": population,
        "inventory_dispositions": records,
        "disposition_counts": dict(sorted(Counter(record["evidence_classification"] for record in records).items())),
        "previously_unclassified_count": sum(record["role"] == "UNCLASSIFIED_CUSTODIAN_METADATA_ONLY" for record in manifest["raw_cache_inventory"]),
        "code_definition_evidence": definitions,
        "archive_search": archive_date_hits(root),
        "runtime_source_constraints": constraints,
        "runtime_history_search": {"reachable_from_inclusive": manifest["observed_head"], "pathspecs": ["*requirements*lock*", "*poetry.lock", "*uv.lock", "*Pipfile.lock", "*environment*.yml", "*deployment*.yaml"], "commit_and_path_lines": [line for line in runtime_history if line], "historical_runtime": "UNKNOWN", "external_archives_accessed": False},
        "fixture_review": "PENDING_HUMAN_REVIEW_NO_SCIENTIFIC_EXECUTION",
        "runner_implementation": "NOT_AVAILABLE_IN_ISOLATED_AUTHORING_CONTEXT",
        "verifier_implementation": "NOT_AVAILABLE_IN_SEPARATE_ISOLATED_AUTHORING_CONTEXT",
        "limitations": ["Disposition covers frozen baseline inventory, not newly discovered or changed source bytes", "No final allowlist or staged-byte artifact created", "Historical source definition references are not execution lineage", "Scoped archive leads do not establish commit/config/runtime", "Runner/verifier/runtime bundles and isolation proof remain external prerequisites"],
    }


def input_review(record: dict[str, Any]) -> dict[str, Any]:
    if record["evidence_classification"] != "UNRESOLVED":
        raise ValueError("input review requires an unresolved baseline record")
    path = record["path"]
    family = "UNDETERMINED"
    definition = None
    if path.startswith("data/shortlists/"):
        family = "STORED_SCAN_OUTPUT_CANDIDATE"
        definition = {"path": "scanner/data_fetcher.py", "symbol": "save_scan_results"}
    elif path.startswith("data/daily_reports/"):
        family = "DOWNSTREAM_REPORT_CANDIDATE"
        definition = {"path": "api/routers/scan.py", "symbol": "save_daily_report"}
    elif path.startswith("data/distribution/"):
        family = "EXPORT_OR_PUBLICATION_CANDIDATE"
    elif path.startswith(("data/tickers/", "data/logs/")):
        family = "POPULATION_OR_LINEAGE_LEAD"
    return {
        "path": path, "snapshot_sha256": record["snapshot_sha256"],
        "original_classification": record["evidence_classification"],
        "candidate_role": family, "historical_writer_reference": definition,
        "role_basis": "HISTORICAL_WRITER_DEFINITION_AND_PATH" if definition else "PATH_ONLY_REQUIRES_CONTENT_AND_OWNER_REVIEW",
        "requiredness": "UNDETERMINED_PENDING_MEMBER_REVIEW",
        "historical_identity": "UNKNOWN", "blind_bundle_allowed": False,
        "final_allowlist_status": record["final_allowlist_status"],
        "review_question": "Required by which V3 target/channel, with which fields and identity evidence? Otherwise document exclusion; do not infer absence of use from a filename.",
    }


def prepare_lock_handoff(root: Path) -> dict[str, Any]:
    for path, expected in ((PROTOCOL, APPROVED_PROTOCOL_SHA256), (BASE_MANIFEST, BASE_MANIFEST_SHA256), (CLOSURE_AUDIT, CLOSURE_AUDIT_SHA256)):
        if artifact_record(root, path)["sha256"] != expected:
            raise ValueError("frozen handoff authority mismatch")
    audit = json.loads(checked_path(root, CLOSURE_AUDIT).read_text(encoding="utf-8"))
    if audit["locked"] or audit["execution_authorized"] or audit["synthetic_gate"] != "NOT_RUN":
        raise ValueError("handoff requires the unexecuted closure baseline")
    reviews = [input_review(record) for record in audit["inventory_dispositions"] if record["evidence_classification"] == "UNRESOLVED"]
    definitions = [code_record(path, git_bytes(root, "show", HISTORICAL_COMMIT + ":" + path)) for path in ("scanner/data_fetcher.py", "api/routers/scan.py")]
    for review in reviews:
        reference = review["historical_writer_reference"]
        if reference and not any(item["path"] == reference["path"] and any(symbol["symbol"] == reference["symbol"] for symbol in item["symbols"]) for item in definitions):
            raise ValueError("historical output writer definition missing")
    gates = [
        ("definitions", "12 item 2; 5", "CUSTODIAN", "Complete producer precision and dependency review at the frozen commit."),
        ("input_authorization", "12 items 3-4; 6", "CUSTODIAN_AND_HUMAN_REVIEWER", "Review each required member/field, optional absence and exclusions; freeze staged bytes, without recovery calculations."),
        ("historical_lineage_runtime", "12 items 2-4, 6; 4", "HISTORICAL_ARCHIVE_OWNER", "Supply original run-to-commit/config/runtime/input/export records; source constraints alone are insufficient."),
        ("fixture_review", "12 item 5; 8", "HUMAN_REVIEWER", "Review the unchanged artificial fixture candidate; no suite execution."),
        ("restricted_implementations", "12 item 6; 7", "SEPARATE_RESTRICTED_AUTHORS", "Provide separately authored runner/verifier and frozen executable suite/runtime bundles."),
        ("isolation", "12 item 7; 7.2-7.3", "ISOLATION_CUSTODIAN_AND_REVIEWER", "Provide effective authoring/compute/execution restrictions and checked canary/access evidence."),
        ("human_lock", "12 items 8-9; 9", "MERIC", "Assign actors/output scope, review all gates and record exact accepted bundle hashes before scientific execution."),
    ]
    return {
        "schema_version": "b2-1-lock-handoff-v1", "layer": "Research", "level": "A",
        "role": "NON_BLIND_CUSTODIAN", "status": "LOCK_BLOCKED",
        "locked": False, "execution_authorized": False, "synthetic_gate": "NOT_RUN",
        "real_execution_performed": False, "blind_execution": {"status": "NOT_VERIFIED"},
        "protocol": {"path": PROTOCOL, "sha256": APPROVED_PROTOCOL_SHA256},
        "closure_baseline": {"path": CLOSURE_AUDIT, "sha256": CLOSURE_AUDIT_SHA256},
        "population": audit["population"], "unresolved_input_reviews": reviews,
        "candidate_role_counts": dict(sorted(Counter(review["candidate_role"] for review in reviews).items())),
        "output_writer_definitions": definitions,
        "gates": [{"id": gate, "protocol_reference": section, "owner_role": owner, "assigned_actor": None, "status": "BLOCKED", "next_action": action, "evidence_artifact": None, "evidence_sha256": None} for gate, section, owner, action in gates],
        "external_archive_delivery": {"original_run_record": None, "commit_config_link": None, "actual_runtime_record": None, "provider_input_export_link": None, "sensitive_values_permitted": False},
        "actors": {"operator": None, "restricted_runner_author": None, "restricted_verifier_author": None, "isolation_custodian": None},
        "limitations": ["Output-writer definitions identify a possible file family, not the actual writer or provenance of every member", "All original unresolved records remain unresolved for member-level requiredness and authorization", "No staged bytes, accepted allowlist, scientific suite or isolated implementation created", "This handoff neither changes V3 nor certifies LOCK readiness"],
    }


def prepare_manifest(root: Path) -> dict[str, Any]:
    protocol = artifact_record(root, PROTOCOL)
    if protocol["sha256"] != APPROVED_PROTOCOL_SHA256:
        raise ValueError("approved protocol identity mismatch")
    observed_head = git_bytes(root, "rev-parse", "HEAD").decode().strip()
    resolved = git_bytes(root, "rev-parse", HISTORICAL_COMMIT + "^{commit}").decode().strip()
    if resolved != HISTORICAL_COMMIT:
        raise ValueError("historical commit identity mismatch")
    exports = []
    for relative in ("data/distribution/scan_export_2026-09-09.json", "data/distribution/scan_export_2026-09-09_published.json"):
        record = artifact_record(root, relative)
        if record["availability"] == "AVAILABLE":
            record["schema_metadata"] = export_schema(checked_path(root, relative))
            if artifact_record(root, relative)["sha256"] != record["sha256"]:
                raise RuntimeError("export changed during schema inspection")
        record.update({"role": "historical_artifact_and_stored_output_candidate", "staged_sha256": None})
        exports.append(record)
    inventory = []
    for relative_root in ("data", "reports", "cache"):
        directory = checked_path(root, relative_root)
        if not directory.is_dir():
            inventory.append({"path": relative_root, "availability": "NOT_FOUND", "role": "inventory_root"})
            continue
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.suffix.lower() not in {".json", ".csv", ".parquet", ".pkl", ".pickle", ".jsonl"}:
                continue
            if path.name.startswith("b2_1_prelock_") or path.name.startswith("b2_1_synthetic_fixtures_"):
                continue
            if any(token in relative.lower() for token in ("secret", "credential", "token", "session", "user", "auth")):
                continue
            record = artifact_record(root, relative)
            if relative.startswith("data/price_cache/"):
                role = "raw_price_candidate"
            elif relative == "data/fundamentals_cache.json":
                role = "external_fundamentals_candidate"
            elif relative.startswith(("reports/", "data/backtest_out/")):
                role = "RESEARCH_RESULT_EXCLUDED_FROM_BLIND_BUNDLE"
            else:
                role = "UNCLASSIFIED_CUSTODIAN_METADATA_ONLY"
            record.update({"role": role, "blind_bundle_allowed": False, "definition_match": "UNKNOWN"})
            inventory.append(record)
    tree = git_bytes(root, "ls-tree", "-r", "--name-only", HISTORICAL_COMMIT, "--", "scanner", "scanner.py", "distribution").decode().splitlines()
    definitions = [code_record(path, git_bytes(root, "show", HISTORICAL_COMMIT + ":" + path)) for path in tree if path.endswith(".py")]
    history = git_bytes(root, "rev-list", "--reverse", observed_head).decode().splitlines()
    history_trees = {}
    revision_tree_map = []
    object_hashes = {}
    for commit in history:
        root_entry = git_bytes(root, "ls-tree", commit, "--", "data").decode().strip()
        tree_id = root_entry.split()[2] if root_entry else None
        revision_tree_map.append({"commit": commit, "data_tree_id": tree_id})
        if tree_id is None or tree_id in history_trees:
            continue
        members = []
        entries = git_bytes(root, "ls-tree", "-r", "-l", "-z", commit, "--", "data")
        for entry in entries.split(b"\0"):
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, object_id, size = metadata.decode().split()
            if kind == "blob" and object_id not in object_hashes:
                object_hashes[object_id] = git_blob_sha256(root, object_id)
            members.append({"path": raw_path.decode(), "git_mode": mode, "git_type": kind, "git_object_id": object_id, "sha256": object_hashes.get(object_id), "bytes": size, "blind_bundle_allowed": False})
        history_trees[tree_id] = {"git_tree_id": tree_id, "members": members}
    fixtures = artifact_record(root, FIXTURES)
    return {
        "schema_version": "b2-1-prelock-candidate-v1",
        "preparation_role": "NON_BLIND_CUSTODIAN_NOT_RUNNER_NOT_VERIFIER",
        "protocol_identity": {"path": PROTOCOL, "approved_sha256": APPROVED_PROTOCOL_SHA256},
        "locked": False, "execution_authorized": False, "real_execution_performed": False,
        "synthetic_gate": "NOT_RUN", "lock_readiness": "BLOCKED",
        "historical_commit_full": HISTORICAL_COMMIT, "observed_head": observed_head,
        "historical_scan_export_candidates": exports, "selected_historical_export": None,
        "raw_cache_inventory": inventory, "historical_code_definitions": definitions,
        "inventory_search": {
            "roots": ["data", "data/backtest_out", "reports", "cache"],
            "current_tree_suffixes": [".json", ".csv", ".parquet", ".pkl", ".pickle", ".jsonl"],
            "revision_population": history, "revision_range": {"root_commits": [commit for commit in history if not git_bytes(root, "rev-list", "--parents", "-n", "1", commit).decode().split()[1:]], "reachable_from_inclusive": observed_head},
            "tracked_data_history_trees": list(history_trees.values()),
            "revision_tree_map": revision_tree_map,
            "history_object_sha256_enumerated": True,
            "completed": False,
            "limits": ["file types outside declared suffixes excluded", "sensitive-name paths excluded", "historical data blob bytes hashed, not parsed or compared", "untracked and dirty files are present-day candidates, not historical proof", "root cache only; alternate cache root absence not established"],
        },
        "synthetic_fixture_candidate": fixtures,
        "runtime_candidate": {"python": platform.python_version(), "implementation": platform.python_implementation(), "historical_runtime_verified": False, "runtime_executable_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(), "historical_dependency_lock": None},
        "blind_execution": {"status": "NOT_VERIFIED", "non_blind_fallback_authorized": False, "runner_bundle_sha256": None, "verifier_bundle_sha256": None, "isolation_evidence_sha256": None, "runtime_and_dependency_manifest_sha256": None},
        "actors": {"operator": None, "independent_verifier": None},
        "approved_output_scope": None,
        "required_blockers": ["historical export selection and lineage", "complete source inventory and classification", "historical call-path dependency closure and runtime identity", "reviewed concrete fixtures", "isolated runner and independent verifier authoring", "frozen runner/verifier/runtime bundles", "enforced isolation evidence", "named actors and exact output scope", "final exact-bundle LOCK approval"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--closure-audit", action="store_true")
    mode.add_argument("--lock-handoff", action="store_true")
    mode.add_argument("--stage-export", action="store_true")
    mode.add_argument("--definition-closure", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not args.output.startswith("reports/b2_1_prelock_") or not args.output.endswith(".json"):
        parser.error("output must be a new reports/b2_1_prelock_*.json artifact")
    output = checked_path(root, args.output)
    if output.exists():
        parser.error("refusing to overwrite an existing preparation artifact")
    prepare = prepare_definition_closure if args.definition_closure else prepare_staged_export if args.stage_export else prepare_lock_handoff if args.lock_handoff else prepare_closure_audit if args.closure_audit else prepare_manifest
    payload = canonical_json(prepare(root))
    with output.open("x", encoding="ascii", newline="\n") as handle:
        handle.write(payload)
    print(canonical_json({"output": args.output, "sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(), "locked": False, "real_execution_performed": False}), end="")


if __name__ == "__main__":
    main()
