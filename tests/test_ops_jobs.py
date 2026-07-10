"""Hafta-1 E5-E7 operasyon job testleri (ağ yok, tmp DB'ler)."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

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
