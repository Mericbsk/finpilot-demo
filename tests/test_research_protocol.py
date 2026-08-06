from argparse import Namespace
from pathlib import Path

import pytest
from research.protocol import (
    CostModel,
    FERRecord,
    LockedHoldoutGuard,
    ProtocolError,
    TemporalSplit,
)
from scripts.research_protocol_check import build_report


def make_record(cost_model: CostModel | None = None, **overrides) -> FERRecord:
    values = {
        "experiment_id": "exp-001",
        "hypothesis": "ATR confirmation improves selection quality",
        "economic_rationale": "Volatility expansion may separate continuation from noise",
        "data_snapshot": "sha256:example",
        "date_range": "2026-01-01/2026-07-31",
        "split": TemporalSplit("2026-04-30", "2026-06-30", "2026-07-31"),
        "factors": ("atr", "confirmation", "volume", "regime"),
        "pairwise_tests": 4,
        "triple_tests": 1,
        "max_interaction_order": 3,
        "cost_model": cost_model or CostModel("cost-v1", 5.0, 8.0, 3.0, 2.0),
        "n_trials": 5,
        "status": "proposed",
    }
    values.update(overrides)
    return FERRecord(**values)


def test_temporal_split_rejects_overlap():
    split = TemporalSplit("2026-06-30", "2026-06-30", "2026-07-31")

    with pytest.raises(ProtocolError, match="train_end"):
        split.validate()


def test_cost_model_requires_all_execution_cost_components():
    model = CostModel("cost-v1", 5.0, None, 3.0, 2.0)

    with pytest.raises(ProtocolError, match="insufficient_data"):
        model.validate()


def test_fer_accepts_multiple_factors_but_rejects_four_way_interaction():
    record = make_record()
    record.validate()
    assert record.as_dict()["factors"] == ["atr", "confirmation", "volume", "regime"]

    with pytest.raises(ProtocolError, match="four-way"):
        make_record(max_interaction_order=4).validate()


def test_fer_rejects_interaction_budget_overages():
    with pytest.raises(ProtocolError, match="25"):
        make_record(pairwise_tests=26).validate()
    with pytest.raises(ProtocolError, match="10"):
        make_record(triple_tests=11).validate()


def test_locked_holdout_can_open_only_once(tmp_path: Path):
    guard = LockedHoldoutGuard(tmp_path / "locked_holdout.json")

    event = guard.open_once("exp-001")

    assert event["experiment_id"] == "exp-001"
    with pytest.raises(ProtocolError, match="already been opened"):
        guard.open_once("exp-002")


def test_protocol_check_reports_missing_cost_data_without_defaults(tmp_path: Path):
    args = Namespace(
        root=tmp_path,
        report_date="2026-08-04",
        experiment_id="exp-missing-cost",
        hypothesis="test hypothesis",
        economic_rationale="test rationale",
        data_snapshot="sha256:example",
        date_range="2026-01-01/2026-07-31",
        train_end="2026-04-30",
        validation_end="2026-06-30",
        locked_oos_end="2026-07-31",
        factor=["atr"],
        pairwise_tests=0,
        triple_tests=0,
        max_interaction_order=1,
        n_trials=1,
        status="proposed",
        cost_model_version="cost-v1",
        commission_bps=None,
        spread_bps=None,
        slippage_bps=None,
        impact_bps=None,
    )

    report = build_report(args)

    cost_gate = next(gate for gate in report["gates"] if gate["name"] == "cost_model")
    assert cost_gate["status"] == "insufficient_data"
    assert report["fer"] is None
