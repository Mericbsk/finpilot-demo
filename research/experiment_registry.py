"""Append-only registry for reproducible research experiments.

This registry is deliberately separate from the model champion registry. It
records hypotheses, test families, budgets and immutable run manifests; it
cannot promote a model or change production behavior.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RegistryError(ValueError):
    """Raised when an immutable research record is invalid or duplicated."""


DEFAULT_PATH = Path("data/research_experiments.db")


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class ExperimentRegistry:
    """SQLite-backed write-once experiment and append-only run registry."""

    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    family_id TEXT NOT NULL,
                    hypothesis TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    planned_tests TEXT NOT NULL,
                    planned_runs INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    record_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS experiment_runs (
                    run_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
                    run_index INTEGER NOT NULL,
                    seed INTEGER NOT NULL,
                    input_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    UNIQUE(experiment_id, run_index)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def register(
        self,
        *,
        experiment_id: str,
        family_id: str,
        hypothesis: str,
        rationale: str,
        planned_tests: list[str],
        planned_runs: int,
    ) -> dict[str, Any]:
        if not all(value.strip() for value in (experiment_id, family_id, hypothesis, rationale)):
            raise RegistryError(
                "experiment identity, family, hypothesis and rationale are required"
            )
        if not planned_tests or planned_runs < 1:
            raise RegistryError("planned tests and planned runs are required")
        record = {
            "experiment_id": experiment_id,
            "family_id": family_id,
            "hypothesis": hypothesis,
            "rationale": rationale,
            "planned_tests": planned_tests,
            "planned_runs": planned_runs,
        }
        envelope = {
            **record,
            "created_at": datetime.now(UTC).isoformat(),
            "record_hash": _record_hash(record),
        }
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        envelope["experiment_id"],
                        envelope["family_id"],
                        envelope["hypothesis"],
                        envelope["rationale"],
                        _canonical_json(envelope["planned_tests"]),
                        envelope["planned_runs"],
                        envelope["created_at"],
                        envelope["record_hash"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise RegistryError(f"experiment already registered: {experiment_id}") from exc
        return envelope

    def record_run(
        self,
        *,
        experiment_id: str,
        run_id: str,
        run_index: int,
        seed: int,
        input_hash: str,
        status: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        if run_index < 0 or not run_id.strip() or not input_hash.strip():
            raise RegistryError("run_id, non-negative run_index and input_hash are required")
        if status not in {"completed", "failed", "insufficient_data"}:
            raise RegistryError(f"unsupported run status: {status}")
        envelope = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "run_index": run_index,
            "seed": seed,
            "input_hash": input_hash,
            "status": status,
            "result": result,
            "created_at": datetime.now(UTC).isoformat(),
        }
        envelope["record_hash"] = _record_hash(envelope)
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO experiment_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        envelope["run_id"],
                        envelope["experiment_id"],
                        envelope["run_index"],
                        envelope["seed"],
                        envelope["input_hash"],
                        envelope["status"],
                        _canonical_json(envelope["result"]),
                        envelope["created_at"],
                        envelope["record_hash"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise RegistryError(f"run already recorded or experiment is unknown: {run_id}") from exc
        return envelope

    def get(self, experiment_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT experiment_id, family_id, hypothesis, rationale, planned_tests, planned_runs, created_at, record_hash "
                "FROM experiments WHERE experiment_id = ?",
                (experiment_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "experiment_id": row[0],
            "family_id": row[1],
            "hypothesis": row[2],
            "rationale": row[3],
            "planned_tests": json.loads(row[4]),
            "planned_runs": row[5],
            "created_at": row[6],
            "record_hash": row[7],
        }

    def budget_report(self) -> dict[str, Any]:
        """Gate 2.2 — experiment budget ledger.

        Reports total configurations run and per-family spend, so the
        multiple-testing budget is visible instead of implicit. A family that
        has consumed many runs without a confirmatory pass is a selection-bias
        risk; this report makes that explicit.
        """
        with self._connect() as connection:
            total_experiments = connection.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
            total_runs = connection.execute("SELECT COUNT(*) FROM experiment_runs").fetchone()[0]
            per_family = connection.execute(
                "SELECT e.family_id, COUNT(DISTINCT e.experiment_id), COUNT(r.run_id) "
                "FROM experiments e LEFT JOIN experiment_runs r "
                "ON e.experiment_id = r.experiment_id GROUP BY e.family_id"
            ).fetchall()
            status_counts = connection.execute(
                "SELECT status, COUNT(*) FROM experiment_runs GROUP BY status"
            ).fetchall()
        return {
            "total_experiments": total_experiments,
            "total_runs": total_runs,
            "per_family": {row[0]: {"experiments": row[1], "runs": row[2]} for row in per_family},
            "run_status_counts": {row[0]: row[1] for row in status_counts},
            "note": "high run counts without a confirmatory pass indicate selection-bias exposure",
        }
