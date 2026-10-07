"""Unit tests for the distribution layer (stdlib-only modules)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Isolate the store DB before importing store-dependent modules.
os.environ["FINPILOT_DIST_DB"] = str(
    Path(tempfile.mkdtemp(prefix="fp_dist_test_")) / "distribution.db"
)

from distribution import broadcast, lint  # noqa: E402
from distribution.concepts import concept_of_the_day  # noqa: E402
from distribution.jobs import _resolve_karne_by_grade  # noqa: E402
from distribution.market_calendar import is_trading_day  # noqa: E402
from distribution.partial_publication import (  # noqa: E402
    build_partial_export,
    build_partial_snapshots,
    load_partial_export,
    load_partial_snapshot,
    save_partial_export,
    save_partial_snapshot,
    validate_partial_export,
    validate_partial_snapshot,
)
from distribution.rationale import build_rationale, extract_badges, prob_band  # noqa: E402
from distribution.scan_contract import full_scan_problems  # noqa: E402
from distribution.schema import (  # noqa: E402
    SCHEMA_VERSION,
    demo_view,
    free_view,
    validate_snapshot,
)
from distribution.snapshot_builder import build_snapshot, read_json_object  # noqa: E402
from distribution.store import ensure_tables, get_conn, log_delivery  # noqa: E402
from distribution.templates import render_daily_free, render_daily_premium  # noqa: E402


def _row(sym: str, conv: str = "A", prob: float = 0.63, **kw) -> dict:
    base = {
        "symbol": sym,
        "price": 12.5,
        "score": 40,
        "composite_score": 55.0,
        "conviction_tier": conv,
        "conviction_prob": prob,
        "tier": "TRIGGER",
        "squeeze_factor": 0.8,
        "volume_spike": True,
        "atr_pct": 5.0,
    }
    base.update(kw)
    return base


class TestLint(unittest.TestCase):
    def test_clean_text_passes(self):
        text = "NVAX bir izleme adayıdır. Yatırım tavsiyesi değildir."
        self.assertEqual(lint.check_text(text), [])
        self.assertTrue(lint.require_disclaimer(text))

    def test_buy_language_blocked(self):
        self.assertTrue(lint.check_text("Bu hisseyi hemen al!"))
        self.assertTrue(lint.check_text("Strong buy on NVAX"))

    def test_price_target_blocked(self):
        self.assertTrue(lint.check_text("Hedef fiyat $20, stop-loss $15"))

    def test_guarantee_and_fomo_blocked(self):
        self.assertTrue(lint.check_text("garantili kazanç"))
        self.assertTrue(lint.check_text("Bu fırsatı kaçırmayın!"))
        self.assertTrue(lint.check_text("don't miss this"))

    def test_assert_publishable_requires_disclaimer(self):
        with self.assertRaises(ValueError):
            lint.assert_publishable("Temiz metin ama disclaimer yok.")


class TestRationale(unittest.TestCase):
    def test_badges_extracted(self):
        badges = extract_badges(_row("ABC"))
        self.assertIn("squeeze", badges)
        self.assertIn("rvol", badges)
        self.assertLessEqual(len(badges), 4)

    def test_rationale_is_clean_and_factual(self):
        r = build_rationale("ABC", "A", ["squeeze", "gap"])
        self.assertIn("ABC", r)
        self.assertEqual(lint.check_text(r), [])

    def test_rationale_explains_factor_combination_and_open_question(self):
        rationale = build_rationale(
            "ABC",
            "C",
            ["rvol", "momentum", "regime"],
            lang="tr",
            context={"date": "2026-07-29"},
        )
        self.assertIn("Bu üç işaret birlikte", rationale)
        self.assertIn("henüz doğrulanmış değil", rationale)
        self.assertEqual(lint.check_text(rationale), [])

    def test_english_rationale_does_not_use_turkish_i_casing(self):
        rationale = build_rationale("ABC", "A", [], lang="en", context={"date": "2026-07-06"})
        self.assertNotIn("İts ", rationale)

    def test_prob_band_rounding(self):
        self.assertEqual(prob_band(0.63), "~65%")
        self.assertEqual(prob_band(0.61), "~60%")
        self.assertEqual(prob_band(0.0), "—")
        self.assertEqual(prob_band(0.99), "~95%")


class TestSnapshot(unittest.TestCase):
    def test_corrupt_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "corrupt.json"
            path.write_bytes(b'{"date":"2026-07-06"}\x00')
            with self.assertRaises(ValueError):
                read_json_object(path)

    def test_build_and_validate(self):
        rows = [_row("AAA"), _row("BBB", conv="B", prob=0.5), _row("CCC", conv="C", prob=0.3)]
        snap = build_snapshot(rows, universe=1812, date_str="2026-07-06")
        self.assertEqual(validate_snapshot(snap), [])
        self.assertEqual(snap["schema"], SCHEMA_VERSION)
        self.assertEqual(snap["candidates"][0]["ticker"], "AAA")
        self.assertFalse(snap["candidates"][0]["premium_only"])
        self.assertTrue(snap["candidates"][2]["premium_only"])
        self.assertEqual(snap["karne"]["toplam_aday_bugun"], {"A": 1, "B": 1, "C": 1})

    def test_ungraded_rows_excluded_but_counted_zero(self):
        rows = [{"symbol": "XXX", "score": 10}]
        snap = build_snapshot(rows, universe=100, date_str="2026-07-06")
        self.assertEqual(snap["candidates"], [])
        self.assertIn("no graded candidates today", snap["warnings"])

    def test_free_view_strips_premium(self):
        rows = [_row(s) for s in ("AAA", "BBB", "CCC", "DDD")]
        snap = build_snapshot(rows, universe=100, date_str="2026-07-06")
        fv = free_view(snap)
        self.assertEqual(len(fv["candidates"]), 2)
        self.assertNotIn("risk_note", fv["candidates"][0])
        self.assertNotIn("factor_detail", fv["candidates"][0])

    def test_public_view_strips_internal_risk_metrics(self):
        snap = build_snapshot([_row("AAA")], universe=100, date_str="2026-07-06")
        public = demo_view(snap, max_candidates=1)
        metrics = public["candidates"][0]["metrics"]
        self.assertIn("price", metrics)
        self.assertNotIn("risk_reward", metrics)
        self.assertNotIn("stop_loss", metrics)
        self.assertNotIn("take_profit", metrics)
        self.assertNotIn("stop_loss_percent", metrics)


class TestPartialPublication(unittest.TestCase):
    def test_partial_artifacts_are_separate_and_keep_full_gate(self):
        rows = [_row("AAA", conv="B"), _row("BBB", conv="C", prob=0.4)]
        export = build_partial_export(
            rows,
            requested_universe=3,
            date_str="2026-10-05",
            source_artifacts=[{"path": "batch.csv", "sha256": "example-hash"}],
        )
        self.assertEqual(export["scan_scope"], "partial")
        self.assertFalse(export["scan_complete"])
        self.assertEqual(validate_partial_export(export), [])
        self.assertTrue(
            full_scan_problems(export["results"], export["universe"], export["scan_complete"])
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir) / "exports"
            snapshot_dir = Path(temp_dir) / "snapshots"
            with (
                patch("distribution.partial_publication.PARTIAL_EXPORT_DIR", export_dir),
                patch("distribution.partial_publication.PARTIAL_SNAPSHOT_DIR", snapshot_dir),
            ):
                export_path = save_partial_export(export)
                loaded_export = load_partial_export("2026-10-05", export["scan_id"])
                self.assertEqual(loaded_export["results"], rows)
                self.assertIn("_partial_", export_path.name)

                snapshots = build_partial_snapshots(
                    rows,
                    requested_universe=3,
                    date_str="2026-10-05",
                    scan_id=export["scan_id"],
                    source_export=export_path.name,
                )
                self.assertEqual(snapshots["tr"]["publication_scope"], "partial")
                self.assertEqual(snapshots["tr"]["result_coverage_pct"], 0.1)
                self.assertEqual(snapshots["tr"]["scan_result_count"], 2)
                self.assertEqual(snapshots["tr"]["snapshot_id"], snapshots["en"]["snapshot_id"])
                for lang, snapshot in snapshots.items():
                    self.assertEqual(validate_partial_snapshot(snapshot), [])
                    save_partial_snapshot(snapshot, lang)
                    loaded = load_partial_snapshot("2026-10-05", export["scan_id"], lang)
                    self.assertEqual(loaded["snapshot_id"], snapshot["snapshot_id"])

    def test_partial_validation_rejects_tampered_identity(self):
        snapshot = build_partial_snapshots(
            [_row("AAA")], requested_universe=2, date_str="2026-10-05"
        )["tr"]
        snapshot["snapshot_id"] = "0" * 24
        self.assertIn(
            "snapshot_id does not match partial snapshot metadata",
            validate_partial_snapshot(snapshot),
        )

    def test_partial_api_exposes_published_file_only(self):
        from api.routers.distribution import distribution_partial_snapshot
        from distribution.snapshot_builder import write_snapshot
        from fastapi import HTTPException

        today = date.today().isoformat()
        snapshot = build_partial_snapshots([_row("AAA")], requested_universe=2, date_str=today)[
            "en"
        ]
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"FINPILOT_DIST_DIR": temp_dir}),
        ):
            dist_dir = Path(temp_dir)
            staged = dist_dir / "partial_snapshots" / "staged.json"
            write_snapshot(staged, snapshot)
            with self.assertRaises(HTTPException):
                distribution_partial_snapshot()

            published = dist_dir / "partial_published" / "snapshot_en_latest.json"
            write_snapshot(published, snapshot)
            result = distribution_partial_snapshot()
            self.assertEqual(result["publication_scope"], "partial")
            self.assertEqual(result["snapshot_id"], snapshot["snapshot_id"])

    def test_public_view_strips_internal_risk_metrics_from_context(self):
        snap = build_snapshot([_row("AAA")], universe=100, date_str="2026-07-06")
        snap["web_context"] = [{"ticker": "CTX", "metrics": {"stop_loss": 10.0, "price": 12.0}}]
        public = demo_view(snap, max_candidates=1)
        metrics = public["web_context"][0]["metrics"]
        self.assertIn("price", metrics)
        self.assertNotIn("stop_loss", metrics)


class TestKarneResolver(unittest.TestCase):
    def test_scorecard_uses_closed_outcomes_only(self):
        result = _resolve_karne_by_grade(
            {
                "by_conviction": [
                    {"group": "A", "count": 5, "tp_count": 2, "stop_count": 1, "open_count": 2},
                    {"group": "B", "count": 3, "tp_count": 0, "stop_count": 0, "open_count": 3},
                ]
            }
        )
        self.assertEqual(result["A"], {"n": 3, "hit_rate": 0.667, "avg_pnl": None})
        self.assertNotIn("B", result)

    def test_resolver_falls_back_to_tier_groups(self):
        result = _resolve_karne_by_grade(
            {"by_conviction": [], "by_tier": [{"group": "C", "tp_count": 1, "stop_count": 2}]}
        )
        self.assertEqual(result["C"]["n"], 3)
        self.assertEqual(result["C"]["hit_rate"], 0.333)


class TestTemplates(unittest.TestCase):
    def _snap(self):
        rows = [_row("AAA"), _row("BBB", conv="B", prob=0.5), _row("CCC", conv="C", prob=0.3)]
        return build_snapshot(rows, universe=1812, date_str="2026-07-06")

    def test_free_brief_lint_clean(self):
        text = render_daily_free(self._snap(), concept_line=concept_of_the_day(date(2026, 7, 6)))
        lint.assert_publishable(text)  # raises on failure
        self.assertIn("Daily Brief", text)
        self.assertIn("toplam", text)
        self.assertIn("Öne çıkaran nedenler:", text)
        self.assertIn("Short baskısı", text)

    def test_premium_brief_lint_clean_and_fuller(self):
        text = render_daily_premium(self._snap())
        lint.assert_publishable(text)
        self.assertIn("CCC", text)  # premium shows all candidates

    def test_free_brief_hides_premium_candidates(self):
        text = render_daily_free(self._snap())
        self.assertNotIn("CCC", text.split("🎯")[0])  # not in candidate section


class TestBroadcastQueue(unittest.TestCase):
    def test_queue_approve_send_flow(self):
        text = "Test brifi. Yatırım tavsiyesi değildir."
        qid = broadcast.queue_draft("daily_free", "2026-07-06", text)
        self.assertGreater(qid, 0)
        pending = broadcast.get_pending()
        self.assertTrue(any(p["id"] == qid for p in pending))

        self.assertTrue(broadcast.decide(qid, approve=True, decided_by="admin"))
        self.assertFalse(broadcast.decide(qid, approve=True, decided_by="admin"))  # idempotent

        approved = broadcast.get_approved_unsent()
        self.assertTrue(any(a["id"] == qid for a in approved))
        log_delivery(qid, "test-channel", True, telegram_message_id=123)
        broadcast.mark_sent(qid)
        self.assertFalse(any(a["id"] == qid for a in broadcast.get_approved_unsent()))

    def test_snapshot_metadata_is_idempotent(self):
        text = "Test brifi. Yatırım tavsiyesi değildir."
        first = broadcast.queue_draft(
            "daily_free",
            "2026-07-07",
            text,
            snapshot_id="snap-1",
            snapshot_date="2026-07-07",
            snapshot_universe=1812,
            candidate_hash="hash-1",
            scan_id="scan-1",
        )
        second = broadcast.queue_draft(
            "daily_free",
            "2026-07-07",
            text,
            snapshot_id="snap-1",
            snapshot_date="2026-07-07",
            snapshot_universe=1812,
            candidate_hash="hash-1",
            scan_id="scan-1",
        )
        self.assertEqual(first, second)
        item = next(row for row in broadcast.get_pending() if row["id"] == first)
        self.assertEqual(item["snapshot_id"], "snap-1")
        self.assertEqual(item["snapshot_scope"], "full")

    def test_partial_queue_scope_and_coverage_metadata(self):
        text = "Kısmi tarama taslağı. Yatırım tavsiyesi değildir."
        queue_id = broadcast.queue_draft(
            "daily_free_partial",
            "2026-10-05",
            text,
            snapshot_id="partial-snap-1",
            snapshot_date="2026-10-05",
            snapshot_universe=1812,
            candidate_hash="partial-hash-1",
            scan_id="partial-scan-1",
            snapshot_scope="partial",
            snapshot_requested_universe=1612,
            snapshot_result_count=1601,
        )
        item = next(row for row in broadcast.get_pending() if row["id"] == queue_id)
        self.assertEqual(item["snapshot_scope"], "partial")
        self.assertEqual(item["snapshot_requested_universe"], 1612)
        self.assertEqual(item["snapshot_result_count"], 1601)

    def test_unknown_snapshot_scope_is_rejected(self):
        with self.assertRaises(ValueError):
            broadcast.queue_draft(
                "daily_free",
                "2026-07-06",
                "Clean text. Yatırım tavsiyesi değildir.",
                snapshot_scope="partialish",
            )

    def test_partial_sent_queue_does_not_increment_full_edition_count(self):
        ensure_tables()
        count_before = broadcast.count_sent_editions()
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO broadcast_queue(kind, brief_date, text, status, created_at, snapshot_scope) "
                "VALUES('daily_free_partial','2026-10-05','partial','sent',1,'partial')"
            )
            conn.execute(
                "INSERT INTO broadcast_queue(kind, brief_date, text, status, created_at, snapshot_scope) "
                "VALUES('daily_free','2026-10-06','full','sent',2,'full')"
            )
        self.assertEqual(broadcast.count_sent_editions(), count_before + 1)

    def test_lint_blocks_queue(self):
        with self.assertRaises(ValueError):
            broadcast.queue_draft("daily_free", "2026-07-06", "Hemen al, garantili kazanç!")


class TestCalendar(unittest.TestCase):
    def test_weekend_and_holiday(self):
        self.assertFalse(is_trading_day(date(2026, 7, 4)))  # Saturday
        self.assertFalse(is_trading_day(date(2026, 7, 3)))  # July 4th observed
        self.assertTrue(is_trading_day(date(2026, 7, 6)))  # Monday


if __name__ == "__main__":
    unittest.main(verbosity=2)
