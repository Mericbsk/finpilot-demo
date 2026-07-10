"""Hafta-1 E2-E4 içerik katmanı testleri."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("FINPILOT_DIST_DB", str(Path(tempfile.mkdtemp(prefix="fp_cl_")) / "d.db"))

from distribution import lint  # noqa: E402
from distribution.concepts import TERMS, concept_of_the_day  # noqa: E402
from distribution.glossary import GLOSSARY  # noqa: E402
from distribution.snapshot_builder import _risk_note  # noqa: E402


class TestGlossary(unittest.TestCase):
    def test_min_30_and_unique(self):
        self.assertGreaterEqual(len(GLOSSARY), 30)
        self.assertEqual(len({e["key"] for e in GLOSSARY}), len(GLOSSARY))
        self.assertEqual(len({e["slug"] for e in GLOSSARY}), len(GLOSSARY))

    def test_all_fields_present_and_lint_clean(self):
        for e in GLOSSARY:
            for f in ("key", "slug", "name_tr", "name_en", "line_tr", "line_en", "card_en"):
                self.assertTrue(e.get(f), f"{e['key']} missing {f}")
            for f in ("line_tr", "line_en", "card_en"):
                self.assertEqual(lint.check_text(e[f]), [], f"lint fail: {e['key']}.{f}: {e[f]}")

    def test_badge_keys_covered(self):
        keys = {e["key"] for e in GLOSSARY}
        for badge in (
            "squeeze",
            "catalyst",
            "rvol",
            "gap",
            "momentum",
            "volume",
            "contraction",
            "regime",
            "early_tier",
        ):
            self.assertIn(badge, keys)

    def test_rotation_no_repeat_over_pool_length(self):
        n = len(TERMS)
        seen = {concept_of_the_day(date(2026, 7, 6) + timedelta(days=i)) for i in range(n)}
        # ordinal artışı ile n gün boyunca hepsi farklı olmalı
        self.assertEqual(len(seen), n)


class TestRiskPool(unittest.TestCase):
    def test_dedupe_within_brief(self):
        used: set[str] = set()
        rows = [{"symbol": f"T{i}", "atr_pct": 7.0} for i in range(3)]  # aynı koşul (high_atr) x3
        notes = [
            _risk_note(r, grade="B", lang="tr", date_str="2026-07-06", used=used) for r in rows
        ]
        self.assertEqual(len(set(notes)), 3, f"tekrar var: {notes}")

    def test_priority_combo(self):
        note = _risk_note(
            {"symbol": "X", "squeeze_factor": 0.9, "price": 3.0},
            grade="B",
            lang="tr",
            date_str="2026-07-06",
            used=set(),
        )
        self.assertIn("düşük fiyat", note)  # squeeze_lowprice havuzu seçilmeli

    def test_deterministic_and_lint_clean(self):
        a = _risk_note({"symbol": "X", "atr_pct": 7.0}, "B", "en", "2026-07-06", set())
        b = _risk_note({"symbol": "X", "atr_pct": 7.0}, "B", "en", "2026-07-06", set())
        self.assertEqual(a, b)
        self.assertEqual(lint.check_text(a), [])


class TestMarketContext(unittest.TestCase):
    def test_missing_sources_yield_empty(self):
        os.environ["FINPILOT_MACRO_CACHE"] = "/nonexistent/macro.json"
        os.environ["FINPILOT_SPY_CACHE"] = "/nonexistent/spy.json"
        import importlib

        import distribution.market_context as mc

        importlib.reload(mc)
        self.assertEqual(mc.build_context_line("tr"), "")
        # temizle
        os.environ.pop("FINPILOT_MACRO_CACHE")
        os.environ.pop("FINPILOT_SPY_CACHE")
        importlib.reload(mc)


if __name__ == "__main__":
    unittest.main(verbosity=1)
