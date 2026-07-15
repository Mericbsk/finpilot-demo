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


# ── factor ablation (which flag to open?) ────────────────────────────────────
def _abl_rec(entry, closes, factor_key, factor_val, highs=None, lows=None):
    return {
        "entry_price": entry,
        "forward_closes": closes,
        "forward_highs": highs,
        "forward_lows": lows,
        factor_key: factor_val,
        "side": "long",
    }


def test_factor_ablation_separates_when_high_bucket_wins():
    from scanner.edge_report import factor_ablation

    # HIGH-squeeze names all win (+12%); LOW-squeeze names all lose (-6%).
    recs = [
        _abl_rec(100, [112], "squeeze_factor", 0.8, highs=[112], lows=[111]) for _ in range(3)
    ] + [_abl_rec(100, [93], "squeeze_factor", 0.1, highs=[94], lows=[93]) for _ in range(3)]
    out = factor_ablation(
        recs, factor_key="squeeze_factor", hi_threshold=0.5, tp_pct=0.10, sl_pct=0.05, max_horizon=3
    )
    assert out["n_hi"] == 3 and out["n_lo"] == 3
    assert out["separates"] is True
    assert out["expectancy_lift"] > 0 and out["tp_rate_lift"] > 0


def test_factor_ablation_no_separation_when_random():
    from scanner.edge_report import factor_ablation

    # Factor uncorrelated with outcome: both buckets mixed → no clean separation.
    recs = [
        _abl_rec(100, [112], "f", 0.9, highs=[112], lows=[111]),  # hi, win
        _abl_rec(100, [93], "f", 0.8, highs=[94], lows=[93]),  # hi, loss
        _abl_rec(100, [112], "f", 0.1, highs=[112], lows=[111]),  # lo, win
        _abl_rec(100, [93], "f", 0.2, highs=[94], lows=[93]),  # lo, loss
    ]
    out = factor_ablation(recs, factor_key="f", hi_threshold=0.5, max_horizon=3)
    assert out["separates"] is False  # equal expectancy → no edge


def test_factor_ablation_skips_missing_factor():
    from scanner.edge_report import factor_ablation

    recs = [
        _abl_rec(100, [112], "f", 0.9, highs=[112], lows=[111]),
        {"entry_price": 100, "forward_closes": [101]},  # no 'f' → skipped
    ]
    out = factor_ablation(recs, factor_key="f", hi_threshold=0.5, max_horizon=3)
    assert out["n_hi"] + out["n_lo"] == 1


# ── ablate_all (full sweep) ──────────────────────────────────────────────────
def test_ablate_all_flags_edge_and_fade():
    from scanner.edge_report import ablate_all

    # edge factor 'squeeze_factor': high→win, low→loss (should help, +1).
    # fade factor 'lottery_factor': high→loss, low→win (should "help" as -1,
    # i.e. high underperforms → penalty justified).
    recs = []
    for _ in range(3):
        recs.append(_abl_rec(100, [112], "squeeze_factor", 0.8, highs=[112], lows=[111]))
        recs[-1]["lottery_factor"] = 0.1  # low lottery on a winner
    for _ in range(3):
        recs.append(_abl_rec(100, [93], "squeeze_factor", 0.1, highs=[94], lows=[93]))
        recs[-1]["lottery_factor"] = 0.8  # high lottery on a loser
    specs = [("squeeze_factor", 0.5, +1), ("lottery_factor", 0.5, -1)]
    out = ablate_all(recs, specs=specs, tp_pct=0.10, sl_pct=0.05, max_horizon=3)
    by = {r["factor"]: r for r in out["factors"]}
    assert by["squeeze_factor"]["helps"] is True  # edge confirmed
    assert by["lottery_factor"]["helps"] is True  # fade confirmed (high worse)
    assert out["baseline"]["n"] == 6


def test_ablate_all_helps_none_when_one_bucket_empty():
    from scanner.edge_report import ablate_all

    recs = [_abl_rec(100, [112], "squeeze_factor", 0.9, highs=[112], lows=[111])]  # all HIGH
    out = ablate_all(recs, specs=[("squeeze_factor", 0.5, +1)], max_horizon=3)
    assert out["factors"][0]["helps"] is None  # no LOW bucket → can't judge


def test_format_ablation_md_renders():
    from scanner.edge_report import ablate_all, format_ablation_md

    recs = [
        _abl_rec(100, [112], "squeeze_factor", 0.9, highs=[112], lows=[111]),
        _abl_rec(100, [93], "squeeze_factor", 0.1, highs=[94], lows=[93]),
    ]
    md = format_ablation_md(ablate_all(recs, specs=[("squeeze_factor", 0.5, +1)], max_horizon=3))
    assert "# Factor Ablation" in md and "Baseline" in md and "squeeze_factor" in md
