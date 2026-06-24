"""Tests for scanner.edge_report — the measurement layer that aggregates
triple-barrier outcomes into hit-rate / expectancy, overall and by tier.

Covers the Edge Report P0 building block from
docs/audit-2026-06-12/10-scanner-analiz-ve-arastirma-degerlendirme.md.
Pure functions; no I/O.
"""

from __future__ import annotations

from scanner.edge_report import build_edge_report, format_edge_report_md


def _rec(entry, closes, highs=None, lows=None, tier="NONE", side="long"):
    return {
        "entry_price": entry,
        "forward_closes": closes,
        "forward_highs": highs,
        "forward_lows": lows,
        "tier": tier,
        "side": side,
    }


def test_edge_report_overall_counts():
    records = [
        _rec(100, [112], highs=[112], lows=[111], tier="SETUP"),  # tp
        _rec(100, [93], highs=[94], lows=[93], tier="WATCH"),  # sl
        _rec(100, [101, 102], tier="SETUP"),  # time (max_horizon)
    ]
    rep = build_edge_report(records, tp_pct=0.10, sl_pct=0.05, max_horizon=2)
    assert rep["n"] == 3
    o = rep["overall"]
    assert o["n"] == 3
    # one tp, one sl, one time
    assert abs(o["tp_rate"] - 1 / 3) < 1e-3
    assert abs(o["sl_rate"] - 1 / 3) < 1e-3
    assert abs(o["time_rate"] - 1 / 3) < 1e-3


def test_edge_report_grouped_by_tier():
    records = [
        _rec(100, [112], highs=[112], lows=[111], tier="SETUP"),  # tp
        _rec(100, [115], highs=[115], lows=[114], tier="SETUP"),  # tp
        _rec(100, [93], highs=[94], lows=[93], tier="WATCH"),  # sl
    ]
    rep = build_edge_report(records, tp_pct=0.10, sl_pct=0.05, max_horizon=5, group_by="tier")
    by = rep["by_tier"]
    assert by["SETUP"]["n"] == 2
    assert by["SETUP"]["tp_rate"] == 1.0  # both SETUP hit tp
    assert by["WATCH"]["n"] == 1
    assert by["WATCH"]["sl_rate"] == 1.0


def test_edge_report_expectancy_sign():
    # All winners → positive expectancy; all losers → negative.
    winners = [_rec(100, [120], highs=[120], lows=[119]) for _ in range(4)]
    rep_w = build_edge_report(winners, tp_pct=0.10, sl_pct=0.05, max_horizon=3, group_by=None)
    assert rep_w["overall"]["expectancy"] > 0

    losers = [_rec(100, [90], highs=[91], lows=[90]) for _ in range(4)]
    rep_l = build_edge_report(losers, tp_pct=0.10, sl_pct=0.05, max_horizon=3, group_by=None)
    assert rep_l["overall"]["expectancy"] < 0


def test_edge_report_handles_bad_record():
    # A malformed record is skipped, not fatal.
    records = [
        _rec(100, [112], highs=[112], lows=[111], tier="SETUP"),
        {"tier": "WATCH"},  # missing entry_price / forward_closes
    ]
    rep = build_edge_report(records, tp_pct=0.10, sl_pct=0.05, max_horizon=3)
    assert rep["n"] == 1


def test_edge_report_empty():
    rep = build_edge_report([], group_by="tier")
    assert rep["n"] == 0
    assert rep["overall"]["n"] == 0


def test_format_edge_report_md_renders():
    records = [_rec(100, [112], highs=[112], lows=[111], tier="SETUP")]
    rep = build_edge_report(records, tp_pct=0.10, sl_pct=0.05, max_horizon=3)
    md = format_edge_report_md(rep, title="Test Edge")
    assert "# Test Edge" in md
    assert "TÜMÜ" in md
    assert "| Grup |" in md
