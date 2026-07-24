"""Regression tests for the scanner-to-distribution contract."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.routers.scan import _persist_distribution_export
from distribution.snapshot_builder import build_snapshot
from scanner import evaluate as scanner_evaluate
from scanner.score_engine import compute_legacy_quality_score, compute_v2_score


class TestScannerContract(unittest.TestCase):
    def test_scan_export_rows_keep_distribution_contract_fields(self):
        export_path = Path("data/distribution/scan_export_latest.json")
        if not export_path.exists():
            self.skipTest("latest full scan export is unavailable")
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        rows = payload.get("results", {})
        row = next(iter(rows.values())) if isinstance(rows, dict) else rows[0]
        required = {
            "symbol",
            "selection_eligible",
            "entry_ok",
            "execution_feasible",
            "data_quality_tier",
            "ranking_method",
            "legacy_quality_score",
            "v2_score",
            "strategy_scores",
        }
        self.assertTrue(required.issubset(row), sorted(required - set(row)))
        self.assertEqual(row["ranking_method"], "legacy_quality")
        self.assertEqual(set(row["strategy_scores"]), {"legacy_quality", "v2"})

    def test_unavailable_symbols_remain_in_full_scan_results(self):
        with patch.object(scanner_evaluate, "daily_dd_breached", return_value=False):
            results = scanner_evaluate.evaluate_symbols_parallel(["MISSING"], use_prefetch=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["symbol"], "MISSING")
        self.assertEqual(results[0]["scan_status"], "unavailable")
        self.assertFalse(results[0]["selection_eligible"])

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
                "price": 12.5,
                "risk_reward": 1.8,
                "data_quality_tier": "Tier 1",
                "ranking_method": "legacy_quality",
                "volume_multiple": 2.1,
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
        self.assertEqual(snapshot["candidates"][0]["metrics"]["price"], 12.5)
        self.assertEqual(snapshot["candidates"][0]["metrics"]["ranking_method"], "legacy_quality")

    def test_partial_export_does_not_replace_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp)
            latest = export_dir / "scan_export_latest.json"
            latest.write_text(
                json.dumps({"date": "2026-07-17", "universe": 1812}), encoding="utf-8"
            )
            with patch.dict(os.environ, {"FINPILOT_DIST_DIR": tmp}, clear=False):
                _persist_distribution_export({"A": {"symbol": "A"}}, universe=12)
            self.assertEqual(json.loads(latest.read_text(encoding="utf-8"))["universe"], 1812)
            today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
            self.assertTrue(list(export_dir.glob(f"scan_export_{today}_partial_*.json")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
