"""Hafta-1 E5-E7 operasyon job testleri (ağ yok, tmp DB'ler)."""

from __future__ import annotations

import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_TMP = Path(tempfile.mkdtemp(prefix="fp_ops_"))
os.environ["FINPILOT_DIST_DB"] = str(_TMP / "distribution.db")
os.environ["FINPILOT_DIST_DIR"] = str(_TMP / "dist")
os.environ["FINPILOT_BACKUP_DIR"] = str(_TMP / "backups")
os.environ["FINPILOT_DB_PATH"] = str(_TMP / "finpilot.db")
os.environ["FINPILOT_ENABLE_DISTRIBUTION"] = "1"

from distribution import (
    jobs,  # noqa: E402
    maintenance,  # noqa: E402
)


def _make_db(path: Path, rows: int = 3) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t(x INTEGER)")
    conn.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(rows)])
    conn.commit()
    conn.close()


class TestUniverseLoader(unittest.TestCase):
    def test_env_override(self):
        os.environ["FINPILOT_SCAN_SYMBOLS"] = "aapl, msft ,nvda"
        try:
            self.assertEqual(jobs._load_universe(), ["AAPL", "MSFT", "NVDA"])
        finally:
            os.environ.pop("FINPILOT_SCAN_SYMBOLS")

    def test_presets_json_fallback(self):
        presets = _TMP / "presets.json"
        presets.write_text(
            json.dumps({"tech": {"big": ["AAPL", "MSFT"], "small": ["IONQ"]}}),
            encoding="utf-8",
        )
        os.environ["FINPILOT_PRESETS_JSON"] = str(presets)
        try:
            self.assertEqual(jobs._load_universe(), ["AAPL", "IONQ", "MSFT"])
        finally:
            os.environ.pop("FINPILOT_PRESETS_JSON")


class TestSentinel(unittest.TestCase):
    def test_sentinel_alerts_when_stale(self):
        alerts: list[str] = []
        orig_notify, orig_fresh, orig_trading = (
            jobs.notify_admin,
            jobs._export_is_fresh,
            jobs.is_trading_day,
        )
        jobs.notify_admin = lambda t: alerts.append(t) or True
        jobs._export_is_fresh = lambda: False
        jobs.is_trading_day = lambda d: True
        try:
            r = jobs.job_scan_sentinel()
            self.assertTrue(r.get("alerted"))
            self.assertEqual(len(alerts), 1)
        finally:
            jobs.notify_admin, jobs._export_is_fresh, jobs.is_trading_day = (
                orig_notify,
                orig_fresh,
                orig_trading,
            )

    def test_sentinel_quiet_when_fresh(self):
        orig_fresh, orig_trading = jobs._export_is_fresh, jobs.is_trading_day
        jobs._export_is_fresh = lambda: True
        jobs.is_trading_day = lambda d: True
        try:
            self.assertEqual(jobs.job_scan_sentinel(), {"ok": True})
        finally:
            jobs._export_is_fresh, jobs.is_trading_day = orig_fresh, orig_trading


class TestBackup(unittest.TestCase):
    def test_backup_integrity_and_verify(self):
        _make_db(Path(os.environ["FINPILOT_DB_PATH"]), rows=5)
        _make_db(Path(os.environ["FINPILOT_DIST_DB"]), rows=2)
        r = maintenance.job_backup(notify=False)
        self.assertTrue(r["ok"], r)
        self.assertTrue(all(v == "ok" for v in r["results"].values()), r)

        v = maintenance.verify_backup()
        self.assertTrue(v["ok"], v)
        self.assertIn("finpilot.db", v["report"])
        self.assertEqual(v["report"]["finpilot.db"]["counts"].get("t"), 5)

    def test_corrupt_db_flagged(self):
        bad = Path(os.environ["FINPILOT_BACKUP_DIR"]) / "2020-01-01"
        bad.mkdir(parents=True, exist_ok=True)
        (bad / "broken.db").write_bytes(b"this is not sqlite")
        self.assertTrue(maintenance._integrity(bad / "broken.db").startswith("ERROR"))


class TestDraftTrigger(unittest.TestCase):
    def setUp(self):
        # Isolate from other tests in this class: clear any "today" rows so
        # the dedup check starts from a known-clean state regardless of
        # test execution order.
        from distribution.store import ensure_tables, get_conn

        ensure_tables()
        today = jobs._vienna_now().date().isoformat()
        with get_conn() as conn:
            conn.execute("DELETE FROM broadcast_queue WHERE brief_date=?", (today,))
            conn.commit()

    def test_skips_small_universe(self):
        r = jobs.maybe_trigger_draft_after_scan(50)
        self.assertEqual(r.get("skipped"), "universe 50 < min 100")

    def test_skips_non_trading_day(self):
        orig_trading = jobs.is_trading_day
        jobs.is_trading_day = lambda d: False
        try:
            r = jobs.maybe_trigger_draft_after_scan(500)
            self.assertEqual(r.get("skipped"), "not a trading day")
        finally:
            jobs.is_trading_day = orig_trading

    def test_dedup_skips_when_already_drafted(self):
        from distribution import broadcast, lint

        orig_trading, orig_draft = jobs.is_trading_day, jobs.job_draft
        jobs.is_trading_day = lambda d: True
        calls: list[int] = []
        jobs.job_draft = lambda: calls.append(1) or {"free_queue_id": 1}
        try:
            today = jobs._vienna_now().date().isoformat()
            broadcast.queue_draft("daily_free", today, f"Test brief.\n\n{lint.DISCLAIMER_TR}")
            r = jobs.maybe_trigger_draft_after_scan(500)
            self.assertEqual(r.get("skipped"), "already drafted today")
            self.assertEqual(calls, [])
        finally:
            jobs.is_trading_day = orig_trading
            jobs.job_draft = orig_draft

    def test_partial_draft_does_not_block_full_daily_draft(self):
        from distribution import broadcast, lint

        today = jobs._vienna_now().date().isoformat()
        broadcast.queue_draft(
            "daily_free_partial",
            today,
            f"Partial draft. {lint.DISCLAIMER_TR}",
            snapshot_scope="partial",
        )
        original = {
            "trading": jobs.is_trading_day,
            "draft": jobs.job_draft,
        }
        jobs.is_trading_day = lambda _date: True
        calls: list[int] = []
        jobs.job_draft = lambda: calls.append(1) or {"free_queue_id": 101}
        try:
            result = jobs.maybe_trigger_draft_after_scan(500)
            self.assertEqual(result, {"free_queue_id": 101})
            self.assertEqual(calls, [1])
        finally:
            jobs.is_trading_day = original["trading"]
            jobs.job_draft = original["draft"]


class TestPublishApprovalGate(unittest.TestCase):
    def test_pending_draft_does_not_push_web_snapshot(self):
        original = {
            "enabled": os.environ.get("FINPILOT_ENABLE_DISTRIBUTION"),
            "push": jobs._push_snapshot_to_web,
            "current": jobs._load_current_snapshot,
            "approved": jobs.broadcast.get_approved_unsent,
            "pending": jobs.broadcast.get_pending,
            "notify": jobs.notify_admin,
        }
        pushed: list[dict | None] = []
        jobs._load_current_snapshot = lambda: {"snapshot_id": "snap-1"}
        jobs._push_snapshot_to_web = lambda snapshot=None: pushed.append(snapshot) or True
        jobs.broadcast.get_approved_unsent = lambda: []
        jobs.broadcast.get_pending = lambda: [{"id": 42}]
        jobs.notify_admin = lambda _text: True
        try:
            result = jobs.job_publish()
            self.assertEqual(result["sent"], [])
            self.assertFalse(result["web_pushed"])
            self.assertEqual(pushed, [])
            self.assertEqual(result["pending_unapproved"], 1)
        finally:
            jobs._push_snapshot_to_web = original["push"]
            jobs._load_current_snapshot = original["current"]
            jobs.broadcast.get_approved_unsent = original["approved"]
            jobs.broadcast.get_pending = original["pending"]
            jobs.notify_admin = original["notify"]

    def test_approved_partial_draft_publishes_only_matching_partial_snapshot(self):
        today = jobs._vienna_now().date().isoformat()
        rows = [
            {
                "symbol": "AAA",
                "price": 12.5,
                "score": 40,
                "composite_score": 55.0,
                "conviction_tier": "B",
                "conviction_prob": 0.6,
                "tier": "CONFIRM",
                "selection_eligible": True,
                "execution_feasible": True,
                "execution_confidence": "Tier 1",
                "squeeze_factor": 0.8,
                "volume_spike": True,
                "atr_pct": 5.0,
            },
            {
                "symbol": "BBB",
                "price": 10.0,
                "score": 30,
                "composite_score": 45.0,
                "conviction_tier": "C",
                "conviction_prob": 0.4,
                "tier": "TRIGGER",
                "selection_eligible": True,
                "execution_feasible": True,
                "execution_confidence": "Tier 1",
                "squeeze_factor": 0.6,
                "volume_spike": False,
                "atr_pct": 6.0,
            },
        ]
        original = {
            "notify": jobs.notify_admin,
            "send": jobs.send_to_channel,
            "mark_sent": jobs.broadcast.mark_sent,
            "get_approved": jobs.broadcast.get_approved_unsent,
            "get_pending": jobs.broadcast.get_pending,
            "current": jobs._load_current_snapshot,
            "push_full": jobs._push_snapshot_to_web,
            "push_partial": jobs._push_partial_snapshot_to_web,
        }
        partial_pushes: list[dict] = []
        full_pushes: list[dict | None] = []
        notices: list[str] = []
        jobs.notify_admin = lambda text: notices.append(text) or True
        draft = jobs.job_partial_draft(
            rows,
            requested_universe=3,
            date_str=today,
            publication_gate_open=False,
        )
        self.assertIn("dağıtım kapalı", notices[0])
        self.assertIn("otomatik Telegram/web yayını yapmaz", notices[0])
        queue_id = draft["free_queue_id"]
        self.assertTrue(jobs.broadcast.decide(queue_id, approve=True, decided_by="test-admin"))
        approved = next(
            item for item in jobs.broadcast.get_approved_unsent() if item["id"] == queue_id
        )
        jobs.broadcast.get_approved_unsent = lambda: [approved]
        jobs.broadcast.get_pending = lambda: []
        jobs._load_current_snapshot = lambda: None
        jobs.send_to_channel = lambda *args, **kwargs: True
        jobs.broadcast.mark_sent = lambda *_args, **_kwargs: None
        jobs._push_snapshot_to_web = lambda snapshot=None: full_pushes.append(snapshot) or True
        jobs._push_partial_snapshot_to_web = (
            lambda snapshot=None: partial_pushes.append(snapshot) or True
        )
        try:
            result = jobs.job_publish()
            self.assertEqual(result["sent"], [queue_id])
            self.assertTrue(result["web_pushed"])
            self.assertEqual(full_pushes, [])
            self.assertEqual(len(partial_pushes), 1)
            self.assertEqual(partial_pushes[0]["snapshot_id"], draft["snapshot_id"])
            self.assertEqual(partial_pushes[0]["lang"], "en")
        finally:
            jobs.notify_admin = original["notify"]
            jobs.send_to_channel = original["send"]
            jobs.broadcast.mark_sent = original["mark_sent"]
            jobs.broadcast.get_approved_unsent = original["get_approved"]
            jobs.broadcast.get_pending = original["get_pending"]
            jobs._load_current_snapshot = original["current"]
            jobs._push_snapshot_to_web = original["push_full"]
            jobs._push_partial_snapshot_to_web = original["push_partial"]

    def test_partial_web_push_preserves_full_snapshot_path(self):
        from distribution.partial_publication import build_partial_snapshots
        from distribution.snapshot_builder import read_json_object

        today = jobs._vienna_now().date().isoformat()
        snapshot = build_partial_snapshots(
            [
                {
                    "symbol": "AAA",
                    "price": 12.5,
                    "score": 40,
                    "composite_score": 55.0,
                    "conviction_tier": "B",
                    "conviction_prob": 0.6,
                    "tier": "CONFIRM",
                    "selection_eligible": True,
                    "execution_feasible": True,
                    "execution_confidence": "Tier 1",
                    "squeeze_factor": 0.8,
                    "volume_spike": True,
                    "atr_pct": 5.0,
                }
            ],
            requested_universe=2,
            date_str=today,
        )["en"]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            full_path = root / "demo_snapshot.json"
            full_path.write_text('{"full":"untouched"}', encoding="utf-8")
            partial_path = root / "demo_partial_snapshot.json"
            data_dir = root / "distribution"
            with (
                patch.object(jobs, "WEB_PUBLIC_SNAPSHOT", full_path),
                patch.object(jobs, "WEB_PUBLIC_PARTIAL_SNAPSHOT", partial_path),
                patch("distribution.snapshot_builder.EXPORT_DIR", data_dir),
            ):
                self.assertTrue(jobs._push_partial_snapshot_to_web(snapshot))
                self.assertEqual(full_path.read_text(encoding="utf-8"), '{"full":"untouched"}')
                self.assertEqual(read_json_object(partial_path)["publication_scope"], "partial")
                self.assertTrue(
                    (data_dir / "partial_published" / "snapshot_en_latest.json").exists()
                )

                jobs.WEB_PUBLIC_PARTIAL_SNAPSHOT = full_path
                self.assertFalse(jobs._push_partial_snapshot_to_web(snapshot))
                self.assertEqual(full_path.read_text(encoding="utf-8"), '{"full":"untouched"}')

    def test_triggers_job_draft_when_no_draft_yet(self):
        orig_trading, orig_draft = jobs.is_trading_day, jobs.job_draft
        jobs.is_trading_day = lambda d: True
        calls: list[int] = []
        jobs.job_draft = lambda: calls.append(1) or {"free_queue_id": 99}
        try:
            r = jobs.maybe_trigger_draft_after_scan(500)
            self.assertEqual(calls, [1])
            self.assertEqual(r.get("free_queue_id"), 99)
        finally:
            jobs.is_trading_day = orig_trading
            jobs.job_draft = orig_draft


class TestWebPublication(unittest.TestCase):
    def test_full_snapshot_has_terminal_newline_without_content_change(self):
        from distribution.schema import demo_view

        snapshot = {
            "date": "2026-10-09",
            "snapshot_id": "test-full-snapshot",
            "universe": 1812,
            "candidates": [],
            "warnings": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "distribution"
            source_dir.mkdir()
            (source_dir / "snapshot_en_latest.json").write_text(
                json.dumps(snapshot), encoding="utf-8"
            )
            public_path = root / "public" / "demo_snapshot.json"
            with (
                patch.object(jobs, "WEB_PUBLIC_SNAPSHOT", public_path),
                patch("distribution.snapshot_builder.EXPORT_DIR", source_dir),
                patch.dict(
                    os.environ,
                    {
                        "FINPILOT_WEB_PUBLISH_CMD": "",
                        "FINPILOT_VERCEL_DEPLOY_HOOK_URL": "",
                        "FINPILOT_REQUIRE_VERCEL_DEPLOY": "0",
                    },
                ),
            ):
                self.assertTrue(jobs._push_snapshot_to_web(snapshot))

            content = public_path.read_bytes()
            self.assertTrue(content.endswith(b"\n"))
            self.assertFalse(content.endswith(b"\n\n"))
            self.assertEqual(json.loads(content), demo_view(snapshot, max_candidates=0))

    def test_commit_failure_includes_hook_stdout_and_complete_stderr(self):
        from scripts import publish_web

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_path = root / "web" / "public" / "demo_snapshot.json"
            snapshot_path.parent.mkdir(parents=True)
            snapshot_path.write_text("{}\n", encoding="utf-8")
            hook_output = "fix end of files...Failed\nfiles were modified by this hook"
            git_error = "line-ending warning\n" * 20 + "complete commit error"
            results = [
                subprocess.CompletedProcess([], 0, "", ""),
                subprocess.CompletedProcess([], 0, "web/public/demo_snapshot.json\n", ""),
                subprocess.CompletedProcess([], 1, hook_output, git_error),
            ]
            output = io.StringIO()
            with (
                patch.object(publish_web, "ROOT", root),
                patch.object(publish_web, "_git", side_effect=results) as mock_git,
                patch("sys.stderr", output),
            ):
                self.assertEqual(publish_web.main(), 1)
                self.assertEqual(mock_git.call_count, 3)
            self.assertIn(hook_output, output.getvalue())
            self.assertIn(git_error, output.getvalue())

    def test_push_failure_includes_error_after_line_ending_warnings(self):
        from scripts import publish_web

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_path = root / "web" / "public" / "demo_snapshot.json"
            snapshot_path.parent.mkdir(parents=True)
            snapshot_path.write_text("{}\n", encoding="utf-8")
            git_error = "line-ending warning\n" * 20 + "fatal: no upstream branch"
            results = [
                subprocess.CompletedProcess([], 0, "", ""),
                subprocess.CompletedProcess([], 0, "web/public/demo_snapshot.json\n", ""),
                subprocess.CompletedProcess([], 0, "commit succeeded", ""),
                subprocess.CompletedProcess([], 128, "push details", git_error),
            ]
            output = io.StringIO()
            with (
                patch.object(publish_web, "ROOT", root),
                patch.object(publish_web, "_git", side_effect=results) as mock_git,
                patch("sys.stderr", output),
            ):
                self.assertEqual(publish_web.main(), 1)
                self.assertEqual(mock_git.call_count, 4)
            self.assertIn("push details", output.getvalue())
            self.assertIn(git_error, output.getvalue())


class TestArchiveCheck(unittest.TestCase):
    def test_skips_non_trading_day(self):
        import distribution.market_calendar as mc

        orig = mc.is_trading_day
        try:
            # maintenance modülü is_trading_day'i çağrı anında import ediyor
            mc.is_trading_day = lambda d: False
            r = maintenance.job_archive_check()
            self.assertIn("skipped", r)
        finally:
            mc.is_trading_day = orig


if __name__ == "__main__":
    unittest.main(verbosity=1)
