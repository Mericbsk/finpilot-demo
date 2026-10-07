"""Collect B2-AUTH evidence without importing production or changing its state.

Output is a derived inventory, not authorization or a scientific verdict.
Only literal Python environment reads are classified; other references need review.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
FLAG_PATTERN = re.compile(
    r"\b(?:FINPILOT_ENABLE_[A-Z0-9_]+|FINPILOT_DRL_GATE|"
    r"FINPILOT_INSTRUMENT_BASELINE|FINPILOT_ALERT_ON_SCAN)\b"
)
SOURCE_DIRS = ("scanner", "distribution", "api", "core", "scripts", "web/src")


def safe_flag_value(value: object) -> str:
    if value is None:
        return "UNSET"
    if value in ("0", "1"):
        return str(value)
    return "NON_BINARY_REDACTED"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_reads(text: str) -> tuple[list[dict], str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], "SYNTAX_ERROR"
    aliases = {"os": "os"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    aliases[alias.asname or alias.name] = "os"
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"os.{alias.name}"

    def qualified(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{qualified(node.value)}.{node.attr}"
        return ""

    reads = []
    for node in ast.walk(tree):
        key = None
        default = None
        kind = None
        if isinstance(node, ast.Call) and qualified(node.func) in ("os.getenv", "os.environ.get"):
            if node.args:
                key = node.args[0]
                default = node.args[1] if len(node.args) > 1 else None
            for keyword in node.keywords:
                if keyword.arg == "key":
                    key = keyword.value
                elif keyword.arg == "default":
                    default = keyword.value
            kind = "LITERAL_ENV_READ"
        elif isinstance(node, ast.Subscript) and qualified(node.value) == "os.environ":
            if isinstance(node.ctx, ast.Load):
                key = node.slice
                kind = "LITERAL_ENV_SUBSCRIPT"
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            continue
        if not FLAG_PATTERN.fullmatch(key.value):
            continue
        default_value = default.value if isinstance(default, ast.Constant) else None
        reads.append(
            {
                "flag": key.value,
                "line": node.lineno,
                "kind": kind,
                "default": safe_flag_value(default_value),
                "default_expression": "DYNAMIC"
                if default is not None and not isinstance(default, ast.Constant)
                else "LITERAL_OR_ABSENT",
            }
        )
    return sorted(reads, key=lambda item: (item["line"], item["flag"])), "PARSED"


def build_inventory(root: Path, process_env: dict | None = None) -> dict:
    config_path = root / ".env"
    local = dotenv_values(config_path, interpolate=False) if config_path.exists() else {}
    process = dict(os.environ) if process_env is None else process_env
    flags = {key for key in set(local) | set(process) if FLAG_PATTERN.fullmatch(key)}
    paths = set(root.glob("*.py"))
    for directory in SOURCE_DIRS:
        base = root / directory
        if base.exists():
            paths.update(
                path
                for path in base.rglob("*")
                if path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}
            )
    files = []
    readers: dict[str, list] = {}
    references: dict[str, list] = {}
    for path in sorted(paths):
        if path.is_symlink() or not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "scripts/b2_auth_readonly_audit.py":
            continue
        text = path.read_text(encoding="utf-8-sig")
        found = set(FLAG_PATTERN.findall(text))
        flags.update(found)
        for number, line in enumerate(text.splitlines(), 1):
            for flag in sorted(set(FLAG_PATTERN.findall(line))):
                references.setdefault(flag, []).append({"path": relative, "line": number})
        reads, parse_state = source_reads(text) if path.suffix == ".py" else ([], "NOT_PYTHON")
        for read in reads:
            readers.setdefault(read["flag"], []).append({"path": relative, **read})
        files.append({"path": relative, "sha256": sha256_file(path), "parse_state": parse_state})
    log_path = root / "docs/governance/decision-log.md"
    log_lines = log_path.read_text(encoding="utf-8-sig").splitlines() if log_path.exists() else []
    inventory = []
    for flag in sorted(flags):
        mentions = [
            number for number, line in enumerate(log_lines, 1) if flag in FLAG_PATTERN.findall(line)
        ]
        inventory.append(
            {
                "flag": flag,
                "scope_class": "ENABLE_FLAG"
                if flag.startswith("FINPILOT_ENABLE_")
                else "ASSOCIATED_CONTROL",
                "local_file_value": safe_flag_value(local.get(flag)),
                "audit_process_value": safe_flag_value(process.get(flag)),
                "production_runtime_value": "UNKNOWN",
                "literal_python_readers": readers.get(flag, []),
                "references": references.get(flag, []),
                "decision_log_literal_mentions": mentions,
                "authorization": "REQUIRES_HUMAN_RECORD_REVIEW",
            }
        )
    return {
        "authority": "DERIVED_EVIDENCE_ONLY",
        "production_action": "NONE",
        "scope": list(SOURCE_DIRS) + ["root/*.py"],
        "limitations": [
            "Literal Python reads are not proof that a branch executed.",
            "Dynamic environment keys and non-Python readers require manual review.",
            "Local .env and audit process are not production runtime evidence.",
            "Decision-log mentions are pointers, never inferred approvals.",
            "No source code, dotenv expressions or production modules are executed.",
        ],
        "local_config_present": config_path.exists(),
        "decision_log_sha256": sha256_file(log_path) if log_path.exists() else None,
        "files": files,
        "flags": inventory,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(build_inventory(args.root.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
