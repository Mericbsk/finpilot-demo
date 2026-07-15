"""Edge Report builder — measurement layer for the early-detection ladder.

P0 deliverable from docs/audit-2026-06-12/10-*: the scanner cannot claim a
signal (or a WATCH/SETUP tier) carries *edge* until its outcomes are labeled by
the triple-barrier method and aggregated into hit-rate / expectancy. This module
turns a batch of signal records (each with a forward price path) into an edge
report, sliced overall and by any grouping key (e.g. ``tier`` or an A/B flag).

Pure / no I/O. The intended wiring (separate, gated step):

    * a scheduler job collects resolved signals from ``outcomes_horizon`` /
      ``signals_archive``, attaches each one's forward OHLC window, and calls
      :func:`build_edge_report` weekly;
    * the result is rendered into the weekly report and the dashboard so the
      early-detection tiers are validated BEFORE any of them influences sizing.

This keeps the discipline from the report: measure first, in shadow mode,
then promote only tiers/factors that show positive post-cost expectancy.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from scanner.labeling import BarrierLabel, summarize_labels, triple_barrier_label


def label_record(
    record: dict[str, Any],
    *,
    tp_pct: float,
    sl_pct: float,
    max_horizon: int | None = None,
) -> BarrierLabel:
    """Label one signal record. Requires ``entry_price`` and ``forward_closes``;
    optional ``forward_highs`` / ``forward_lows`` / ``side``."""
    return triple_barrier_label(
        record["forward_closes"],
        entry_price=float(record["entry_price"]),
        tp_pct=tp_pct,
        sl_pct=sl_pct,
        max_horizon=max_horizon,
        side=record.get("side", "long"),
        forward_highs=record.get("forward_highs"),
        forward_lows=record.get("forward_lows"),
    )


def build_edge_report(
    records: Sequence[dict[str, Any]],
    *,
    tp_pct: float = 0.10,
    sl_pct: float = 0.05,
    max_horizon: int | None = 10,
    group_by: str | None = "tier",
) -> dict[str, Any]:
    """Label every record and aggregate edge statistics.

    Args:
        records: each a dict with ``entry_price`` + ``forward_closes`` (and
                 optional ``forward_highs``/``forward_lows``/``side`` plus any
                 grouping key such as ``tier``).
        tp_pct/sl_pct/max_horizon: barrier parameters.
        group_by: record key to slice by (e.g. "tier"). None → overall only.

    Returns:
        {
          "n": int,
          "params": {...},
          "overall": <summarize_labels dict>,
          "by_<group_by>": { value: <summarize_labels dict>, ... }   # if group_by
        }
    """
    labels: list[BarrierLabel] = []
    grouped: dict[Any, list[BarrierLabel]] = {}

    for rec in records:
        try:
            lab = label_record(rec, tp_pct=tp_pct, sl_pct=sl_pct, max_horizon=max_horizon)
        except Exception:
            continue
        labels.append(lab)
        if group_by is not None:
            key = rec.get(group_by, "UNKNOWN")
            grouped.setdefault(key, []).append(lab)

    report: dict[str, Any] = {
        "n": len(labels),
        "params": {"tp_pct": tp_pct, "sl_pct": sl_pct, "max_horizon": max_horizon},
        "overall": summarize_labels(labels),
    }
    if group_by is not None:
        report[f"by_{group_by}"] = {
            k: summarize_labels(v) for k, v in sorted(grouped.items(), key=lambda kv: str(kv[0]))
        }
    return report


def format_edge_report_md(report: dict[str, Any], *, title: str = "Edge Report") -> str:
    """Render an edge report dict as a compact Markdown table block."""
    lines = [f"# {title}", ""]
    p = report.get("params", {})
    lines.append(
        f"_n={report.get('n', 0)} · TP={p.get('tp_pct')} · SL={p.get('sl_pct')} "
        f"· horizon={p.get('max_horizon')}_"
    )
    lines.append("")
    lines.append("| Grup | n | TP% | SL% | Time% | Ort.Getiri | Beklenti |")
    lines.append("|---|---|---|---|---|---|---|")

    def _row(name: str, s: dict[str, Any]) -> str:
        return (
            f"| {name} | {s['n']} | {s['tp_rate']:.0%} | {s['sl_rate']:.0%} "
            f"| {s['time_rate']:.0%} | {s['avg_ret_pct']:+.2%} | {s['expectancy']:+.2%} |"
        )

    lines.append(_row("TÜMÜ", report["overall"]))
    for gkey in (k for k in report if k.startswith("by_")):
        for name, s in report[gkey].items():
            lines.append(_row(str(name), s))
    return "\n".join(lines)


def factor_ablation(
    records: Sequence[dict[str, Any]],
    *,
    factor_key: str,
    hi_threshold: float,
    tp_pct: float = 0.10,
    sl_pct: float = 0.05,
    max_horizon: int | None = 10,
) -> dict[str, Any]:
    """Split labeled records into HIGH vs LOW buckets by one factor and compare.

    Answers the "which flag to open?" question: does this factor actually
    separate winners from losers on the real signal set? Records that lack a
    numeric ``factor_key`` are skipped.

    Args:
        records: dicts with ``entry_price`` + ``forward_closes`` (+ optional
                 ``forward_highs``/``forward_lows``/``side``) and the factor
                 value under ``factor_key`` (e.g. record["squeeze_factor"]).
        factor_key: which factor to bucket on.
        hi_threshold: value at/above which a record is in the HIGH bucket.

    Returns:
        {factor, threshold, n_hi, n_lo, hi<stats>, lo<stats>, expectancy_lift,
         tp_rate_lift, separates}. ``separates`` is True only when BOTH buckets
         are non-empty AND the HIGH bucket has higher expectancy AND higher
         tp-rate than LOW — a necessary (not sufficient) sign the factor helps.
         Statistical significance / sample size are judged downstream.
    """
    hi: list[dict[str, Any]] = []
    lo: list[dict[str, Any]] = []
    for rec in records:
        try:
            v = float(rec.get(factor_key))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        (hi if v >= hi_threshold else lo).append(rec)

    def _stats(rs: list[dict[str, Any]]) -> dict[str, Any]:
        labels: list[BarrierLabel] = []
        for r in rs:
            try:
                labels.append(
                    label_record(r, tp_pct=tp_pct, sl_pct=sl_pct, max_horizon=max_horizon)
                )
            except Exception:
                continue
        return summarize_labels(labels)

    shi = _stats(hi)
    slo = _stats(lo)
    exp_lift = round(shi["expectancy"] - slo["expectancy"], 6)
    tp_lift = round(shi["tp_rate"] - slo["tp_rate"], 4)
    separates = bool(shi["n"] > 0 and slo["n"] > 0 and exp_lift > 0 and tp_lift > 0)
    return {
        "factor": factor_key,
        "threshold": hi_threshold,
        "n_hi": shi["n"],
        "n_lo": slo["n"],
        "hi": shi,
        "lo": slo,
        "expectancy_lift": exp_lift,
        "tp_rate_lift": tp_lift,
        "separates": separates,
    }


# Default factor specs for a full sweep. direction=+1 → HIGH bucket should be
# BETTER (edge signal); direction=-1 → HIGH bucket should be WORSE (fade/penalty
# factor, e.g. lottery/overnight-gap — the model SUBTRACTS them, so confirming
# them means the high bucket underperforms).
DEFAULT_FACTOR_SPECS: list[tuple[str, float, int]] = [
    ("composite_score", 55.0, +1),  # core: does a higher score → better outcome?
    ("squeeze_factor", 0.5, +1),
    ("catalyst_factor", 0.3, +1),
    ("contraction_factor", 0.6, +1),
    ("rvol_acceleration", 0.3, +1),
    ("sentiment", 0.6, +1),
    ("news_sentiment", 0.6, +1),
    ("conviction_prob", 0.6, +1),
    ("lottery_factor", 0.5, -1),  # fade: HIGH should underperform
    ("overnight_gap_factor", 0.5, -1),  # fade: HIGH should underperform
]


def ablate_all(
    records: Sequence[dict[str, Any]],
    *,
    specs: Sequence[tuple[str, float, int]] = DEFAULT_FACTOR_SPECS,
    tp_pct: float = 0.10,
    sl_pct: float = 0.05,
    max_horizon: int | None = 10,
) -> dict[str, Any]:
    """Run factor_ablation over every factor in ``specs`` + an overall baseline.

    ``helps`` is direction-aware: for an edge factor (direction +1) it is the
    ablation's ``separates``; for a fade/penalty factor (direction -1) it is
    True when the HIGH bucket UNDERperforms (negative expectancy & tp lifts) —
    i.e. the penalty is justified. Only factors present in the data are scored.
    """
    labels = [
        label_record(r, tp_pct=tp_pct, sl_pct=sl_pct, max_horizon=max_horizon)
        for r in records
        if _labelable(r)
    ]
    baseline = summarize_labels(labels)
    rows: list[dict[str, Any]] = []
    for key, thr, direction in specs:
        a = factor_ablation(
            records,
            factor_key=key,
            hi_threshold=thr,
            tp_pct=tp_pct,
            sl_pct=sl_pct,
            max_horizon=max_horizon,
        )
        if a["n_hi"] == 0 or a["n_lo"] == 0:
            helps = None  # not enough data to judge
        elif direction >= 0:
            helps = a["separates"]
        else:
            helps = bool(a["expectancy_lift"] < 0 and a["tp_rate_lift"] < 0)
        rows.append(
            {
                "factor": key,
                "direction": direction,
                "threshold": thr,
                "n_hi": a["n_hi"],
                "n_lo": a["n_lo"],
                "hi_exp": a["hi"]["expectancy"],
                "lo_exp": a["lo"]["expectancy"],
                "expectancy_lift": a["expectancy_lift"],
                "tp_rate_lift": a["tp_rate_lift"],
                "helps": helps,
            }
        )
    return {
        "baseline": baseline,
        "factors": rows,
        "params": {"tp_pct": tp_pct, "sl_pct": sl_pct, "max_horizon": max_horizon},
    }


def _labelable(r: dict[str, Any]) -> bool:
    return "entry_price" in r and "forward_closes" in r and bool(r.get("forward_closes"))


def format_ablation_md(result: dict[str, Any], *, title: str = "Factor Ablation") -> str:
    """Render ablate_all() output as a Markdown decision table."""
    b = result["baseline"]
    lines = [
        f"# {title}",
        "",
        f"_Baseline (all signals): n={b['n']} · hit-rate={b['tp_rate']:.0%} · "
        f"expectancy={b['expectancy']:+.2%}_",
        "",
        "| Faktör | yön | n_hi | n_lo | hi bek. | lo bek. | fark | katkı? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in result["factors"]:
        d = "edge" if r["direction"] >= 0 else "fade"
        helps = "—" if r["helps"] is None else ("✅ EVET" if r["helps"] else "hayır")
        lines.append(
            f"| {r['factor']} | {d} | {r['n_hi']} | {r['n_lo']} | "
            f"{r['hi_exp']:+.2%} | {r['lo_exp']:+.2%} | {r['expectancy_lift']:+.2%} | {helps} |"
        )
    return "\n".join(lines)
