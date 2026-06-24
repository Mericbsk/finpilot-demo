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
