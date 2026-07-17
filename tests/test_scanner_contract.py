"""Regression tests for the scanner-to-distribution contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from distribution.snapshot_builder import build_snapshot
from scanner.score_engine import compute_legacy_quality_score, compute_v2_score


class TestScannerContract(unittest.TestCase):
    def test_legacy_and_v2_scores_are_available(self):
        legacy = compute_legacy_quality_score(
            regime=True,
            direction=True,
            raw_score=3,
            atr_pct=4.0,
            rvol=2.0,
            squeeze_factor=0.5,
        )
        v2 = compute_v2_score(
            gap_factor=0.5,
            rvol_factor=0.5,
            atr_pct=4.0,
            squeeze_factor=0.5,
        )
        self.assertGreater(legacy, 0)
        self.assertEqual(v2, 62)

    def test_snapshot_requires_eligible_execution_ready_rows(self):
        rows = [
            {
                "symbol": "GOOD",
                "conviction_tier": "B",
                "conviction_prob": 0.55,
                "selection_eligible": True,
                "execution_feasible": True,
                "position_cap_reject_reason": None,
            },
            {
                "symbol": "SIGNAL_ONLY",
                "conviction_tier": "A",
                "conviction_prob": 0.7,
                "selection_eligible": False,
                "execution_feasible": True,
            },
            {
                "symbol": "CAP_REJECTED",
                "conviction_tier": "A",
                "conviction_prob": 0.7,
                "selection_eligible": True,
                "execution_feasible": True,
                "position_cap_reject_reason": "adv_position_cap",
            },
        ]
        snapshot = build_snapshot(rows, universe=1812, date_str="2026-07-17")
        self.assertEqual([row["ticker"] for row in snapshot["candidates"]], ["GOOD"])
        self.assertEqual(snapshot["scan_result_count"], 3)
        self.assertEqual(snapshot["eligible_candidate_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
