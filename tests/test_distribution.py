"""Unit tests for the distribution layer (stdlib-only modules)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Isolate the store DB before importing store-dependent modules.
os.environ["FINPILOT_DIST_DB"] = str(
    Path(tempfile.mkdtemp(prefix="fp_dist_test_")) / "distribution.db"
)

from distribution import broadcast, lint  # noqa: E402
from distribution.concepts import concept_of_the_day  # noqa: E402
from distribution.market_calendar import is_trading_day  # noqa: E402
from distribution.rationale import build_rationale, extract_badges, prob_band  # noqa: E402
from distribution.schema import SCHEMA_VERSION, free_view, validate_snapshot  # noqa: E402
from distribution.snapshot_builder import build_snapshot  # noqa: E402
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

    def test_prob_band_rounding(self):
        self.assertEqual(prob_band(0.63), "~65%")
        self.assertEqual(prob_band(0.61), "~60%")
        self.assertEqual(prob_band(0.0), "—")
        self.assertEqual(prob_band(0.99), "~95%")


class TestSnapshot(unittest.TestCase):
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
        broadcast.mark_sent(qid)
        self.assertFalse(any(a["id"] == qid for a in broadcast.get_approved_unsent()))

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
