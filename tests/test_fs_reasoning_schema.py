"""
Tests for the FinSense reasoning-layer schema (fs_cases/fs_predictions/
fs_outcomes/fs_evaluations) — VS-01 Phase 1.

See docs/strategy/FinSense_Vertical_Slice_Specification_v1_2026-08-11.md §1, §8
(Phase 1 Definition of Done) for the checklist these tests cover.
"""

from __future__ import annotations

import sqlite3

import pytest
from auth.database import Database


@pytest.fixture()
def db(tmp_path):
    db_path = str(tmp_path / "fs_schema_test.db")
    database = Database(db_path=db_path)
    database.initialize()
    return database


class TestTablesExist:
    """Database: all four fs_ tables are created by initialize()."""

    @pytest.mark.parametrize(
        "table",
        ["fs_cases", "fs_predictions", "fs_outcomes", "fs_evaluations"],
    )
    def test_table_exists(self, db, table):
        with db.connection() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
        assert row is not None, f"{table} was not created by Database.initialize()"

    def test_restart_preserves_tables(self, tmp_path):
        """Database: tables survive a process restart (re-open same file)."""
        db_path = str(tmp_path / "fs_restart_test.db")
        Database(db_path=db_path).initialize()

        # Simulate restart: new Database instance, same file, initialize() again
        # (idempotent — CREATE TABLE IF NOT EXISTS) must not wipe existing rows.
        db2 = Database(db_path=db_path)
        with db2.connection() as conn:
            conn.execute(
                "INSERT INTO fs_cases (id, asset, event_timestamp, snapshot, context, "
                "horizon_days, outcome_rule, created_at) VALUES "
                "('c1','NVDA','2026-06-12T14:30:00Z','{}','ctx',5,'{}','2026-06-12T14:30:00Z')"
            )
        db2.initialize()  # re-run init, must be idempotent

        with db2.connection() as conn:
            row = conn.execute("SELECT id FROM fs_cases WHERE id='c1'").fetchone()
        assert row is not None, "fs_cases row lost across re-initialize (not idempotent)"


class TestConstraints:
    """Integrity: unique constraint, CHECK constraints, FKs — Phase 1 DoD."""

    def _insert_case(self, conn, case_id="c1"):
        conn.execute(
            "INSERT INTO fs_cases (id, asset, event_timestamp, snapshot, context, "
            "horizon_days, outcome_rule, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (case_id, "NVDA", "2026-06-12T14:30:00Z", "{}", "ctx", 5, "{}", "2026-06-12T14:30:00Z"),
        )

    def test_unique_user_case_prediction(self, db):
        """UNIQUE(anonymous_user_id, case_id): second prediction for the same
        user+case must fail at the DB layer — this is what the API's 409 rests on."""
        with db.connection() as conn:
            self._insert_case(conn)
            conn.execute(
                "INSERT INTO fs_predictions (id, case_id, anonymous_user_id, direction, "
                "probability, reason, committed_at, created_at) VALUES "
                "('p1','c1','anon-1','UP',0.7,'reasoning text here','t1','t1')"
            )
        with pytest.raises(sqlite3.IntegrityError), db.connection() as conn:
            conn.execute(
                "INSERT INTO fs_predictions (id, case_id, anonymous_user_id, direction, "
                "probability, reason, committed_at, created_at) VALUES "
                "('p2','c1','anon-1','DOWN',0.6,'changed my mind','t2','t2')"
            )

    def test_probability_range_check(self, db):
        with db.connection() as conn:
            self._insert_case(conn)
        with pytest.raises(sqlite3.IntegrityError), db.connection() as conn:
            conn.execute(
                "INSERT INTO fs_predictions (id, case_id, anonymous_user_id, direction, "
                "probability, reason, committed_at, created_at) VALUES "
                "('p3','c1','anon-2','UP',1.7,'reasoning text here','t1','t1')"
            )

    def test_direction_check(self, db):
        with db.connection() as conn:
            self._insert_case(conn)
        with pytest.raises(sqlite3.IntegrityError), db.connection() as conn:
            conn.execute(
                "INSERT INTO fs_predictions (id, case_id, anonymous_user_id, direction, "
                "probability, reason, committed_at, created_at) VALUES "
                "('p4','c1','anon-3','SIDEWAYS',0.5,'reasoning text here','t1','t1')"
            )

    def test_outcome_case_fk(self, db):
        """fs_outcomes.case_id -> fs_cases(id)."""
        with db.connection() as conn:
            self._insert_case(conn)
            conn.execute(
                "INSERT INTO fs_outcomes (case_id, actual_direction, resolution_method, "
                "resolved_at) VALUES ('c1','DOWN','finpilot_barrier','t3')"
            )
            row = conn.execute("SELECT case_id FROM fs_outcomes WHERE case_id='c1'").fetchone()
        assert row is not None

    def test_evaluation_prediction_fk(self, db):
        """fs_evaluations.prediction_id -> fs_predictions(id)."""
        with db.connection() as conn:
            self._insert_case(conn)
            conn.execute(
                "INSERT INTO fs_predictions (id, case_id, anonymous_user_id, direction, "
                "probability, reason, committed_at, created_at) VALUES "
                "('p5','c1','anon-4','UP',0.7,'reasoning text here','t1','t1')"
            )
            conn.execute(
                "INSERT INTO fs_evaluations (prediction_id, direction_correct, "
                "binary_outcome, probability_error, created_at) VALUES "
                "('p5', 0, 0, 0.7, 't4')"
            )
            row = conn.execute(
                "SELECT prediction_id FROM fs_evaluations WHERE prediction_id='p5'"
            ).fetchone()
        assert row is not None


class TestIndexes:
    def test_expected_indexes_exist(self, db):
        with db.connection() as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        names = {r[0] for r in rows}
        for expected in (
            "idx_fs_predictions_user",
            "idx_fs_predictions_case",
            "idx_fs_evaluations_prediction",
            "idx_fs_cases_status",
        ):
            assert expected in names, f"missing index {expected}"


class TestExistingSystemsUntouched:
    """Adding fs_* tables must not disturb existing tables (academy, quiz_scores,
    auth users/sessions, signals) — VS-01 Phase 1 DoD explicitly requires this."""

    def test_existing_tables_still_present(self, db):
        with db.connection() as conn:
            rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        names = {r[0] for r in rows}
        for expected in ("users", "sessions", "quiz_scores", "signals", "watchlists"):
            assert expected in names, f"pre-existing table {expected} missing after fs_ migration"
