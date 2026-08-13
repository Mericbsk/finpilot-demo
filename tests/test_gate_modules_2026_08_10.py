"""Contract tests for the five gate modules (Level A)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from research import feature_lineage, null_preflight_gate, restatement_detector, signal_half_life
from research.experiment_registry import ExperimentRegistry


def test_feature_lineage_marks_forward_fields() -> None:
    fwd = feature_lineage.forward_looking_fields()
    assert "resolved_pct_t5" in fwd
    assert "c2c_5d" in fwd
    assert "mae_t5" in fwd
    assert "rvol" not in fwd


def test_feature_lineage_validate_detects_leakage() -> None:
    ok = feature_lineage.validate_feature_set(["rvol", "gap_pct", "atr_pct_real"])
    assert ok["ok"] is True
    bad = feature_lineage.validate_feature_set(["rvol", "c2c_5d"])
    assert bad["ok"] is False
    assert "c2c_5d" in bad["leaked_forward_fields"]
    unknown = feature_lineage.validate_feature_set(["nonexistent_feature"])
    assert "nonexistent_feature" in unknown["unknown_fields"]


def test_restatement_detector_finds_drift() -> None:
    ref = {"2026-01-01": {"date": "2026-01-01", "close": 100.0}}
    cur_same = {"2026-01-01": {"date": "2026-01-01", "close": 100.0}}
    cur_drift = {"2026-01-01": {"date": "2026-01-01", "close": 105.0}}
    assert restatement_detector.detect_restatements(ref, cur_same) == []
    drifted = restatement_detector.detect_restatements(ref, cur_drift)
    assert len(drifted) == 1
    assert abs(drifted[0]["abs_change_pct"] - 5.0) < 1e-6


def test_null_preflight_gate_verdicts() -> None:
    rng = np.random.default_rng(1)
    null = rng.normal(0, 1, 1000).tolist()
    # Candidate far outside null -> finding
    v = null_preflight_gate.null_preflight_gate(5.0, null)
    assert v.status == "finding"
    # Candidate inside null -> discovery signal
    v2 = null_preflight_gate.null_preflight_gate(0.1, null)
    assert v2.status == "discovery_signal"
    # Too few nulls -> insufficient
    v3 = null_preflight_gate.null_preflight_gate(5.0, [0.1, 0.2])
    assert v3.status == "insufficient_data"
    # None candidate -> insufficient
    v4 = null_preflight_gate.null_preflight_gate(None, null)
    assert v4.status == "insufficient_data"


def test_signal_half_life_fast_decay() -> None:
    # Day1 captures most of the day5 move -> fast decay
    n = 200
    df = pd.DataFrame(
        {
            "entry_ok": [True] * n,
            "c2c_1d": np.full(n, 1.0),
            "c2c_5d": np.full(n, 1.2),
        }
    )
    out = signal_half_life.signal_half_life(df)
    assert out["status"] == "completed"
    assert out["day1_share_of_day5_median"] > 0.5
    assert "fast decay" in out["interpretation"]


def test_signal_half_life_insufficient() -> None:
    df = pd.DataFrame({"entry_ok": [True] * 10, "c2c_1d": [1.0] * 10, "c2c_5d": [1.0] * 10})
    out = signal_half_life.signal_half_life(df)
    assert out["status"] == "insufficient_data"


def test_budget_report_counts(tmp_path) -> None:
    reg = ExperimentRegistry(tmp_path / "reg.db")
    reg.register(
        experiment_id="e1",
        family_id="f1",
        hypothesis="h",
        rationale="r",
        planned_tests=["t1"],
        planned_runs=10,
    )
    reg.record_run(
        experiment_id="e1",
        run_id="r1",
        run_index=0,
        seed=1,
        input_hash="abc",
        status="completed",
        result={"x": 1},
    )
    report = reg.budget_report()
    assert report["total_experiments"] == 1
    assert report["total_runs"] == 1
    assert report["per_family"]["f1"]["runs"] == 1
    assert report["run_status_counts"]["completed"] == 1
