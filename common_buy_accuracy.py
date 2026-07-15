#!/usr/bin/env python3
"""Measure common legacy/V2 buy recommendations across the full common timeline."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import UTC, datetime

from p0_execution_replay import (
    DISCOVERY_END,
    VALIDATION_END,
    common_symbol_days,
    load_legacy,
    load_v2,
    percentile_cut,
)
from score_formula_comparison import add_scores, canonical

ROOT = os.path.dirname(os.path.abspath(__file__))
LEGACY_CSV = os.path.join(ROOT, "data", "backtest_out", "full_universe_enriched.csv")
V2_CSV = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v3.csv")
DEFAULT_OUT = os.path.join(ROOT, "data", "backtest_out", "common_buy_accuracy")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-csv", default=LEGACY_CSV)
    parser.add_argument("--v2-csv", default=V2_CSV)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    legacy, v2, universe = common_symbol_days(load_legacy(args.legacy_csv), load_v2(args.v2_csv))
    legacy = add_scores(canonical(legacy))
    v2 = add_scores(canonical(v2))
    legacy_cut = percentile_cut(
        [row for row in legacy if row["date"] <= DISCOVERY_END], "legacy_quality", 0.10
    )
    v2_cut = percentile_cut(
        [row for row in v2 if row["date"] <= DISCOVERY_END], "v2_confirmation", 0.10
    )
    legacy_by_key = {(row["symbol"], row["date"]): row for row in legacy}
    v2_by_key = {(row["symbol"], row["date"]): row for row in v2}

    rows = []
    for key in sorted(legacy_by_key.keys() & v2_by_key.keys()):
        legacy_row = legacy_by_key[key]
        v2_row = v2_by_key[key]
        legacy_buy = (
            legacy_row.get("legacy_quality") is not None
            and legacy_row["legacy_quality"] >= legacy_cut
        )
        v2_buy = (
            v2_row.get("v2_confirmation") is not None
            and v2_row["v2_confirmation"] >= v2_cut
            and all(v2_row.get(field) is not None for field in ("short", "atr", "gap", "rvol"))
        )
        if not (legacy_buy and v2_buy):
            continue
        legacy_correct = bool(legacy_row["target"])
        v2_correct = bool(v2_row["target"])
        rows.append(
            {
                "symbol": key[0],
                "date": key[1],
                "legacy_score": legacy_row["legacy_quality"],
                "v2_score": v2_row["v2_confirmation"],
                "legacy_ret5_pct": legacy_row["ret5"],
                "v2_ret5_pct": v2_row["ret5"],
                "legacy_correct": legacy_correct,
                "v2_correct": v2_correct,
                "both_correct": legacy_correct and v2_correct,
                "period": "discovery"
                if key[1] <= DISCOVERY_END
                else "validation"
                if key[1] <= VALIDATION_END
                else "locked_oos",
            }
        )

    def rate(field: str) -> float | None:
        return round(sum(row[field] for row in rows) / len(rows) * 100.0, 4) if rows else None

    def section(items: list[dict]) -> dict:
        def item_rate(field: str) -> float | None:
            return (
                round(sum(row[field] for row in items) / len(items) * 100.0, 4) if items else None
            )

        return {
            "common_buy_n": len(items),
            "common_buy_dates": len({row["date"] for row in items}),
            "legacy_accuracy_pct": item_rate("legacy_correct"),
            "v2_accuracy_pct": item_rate("v2_correct"),
            "both_correct_pct": item_rate("both_correct"),
        }

    summary = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "definition": "common AL = both fixed discovery top10 score cuts pass on the same canonical symbol-day; target = resolved_pct_t5 >= 5%",
        "common_universe": universe,
        "split": {
            "discovery_end": DISCOVERY_END,
            "validation_end": VALIDATION_END,
            "locked_oos_start_exclusive": VALIDATION_END,
        },
        "cuts": {"legacy_quality": legacy_cut, "v2_confirmation": v2_cut},
        "summary": {
            "all_periods_in_sample": section(rows),
            "after_discovery": section([row for row in rows if row["period"] != "discovery"]),
            "validation_plus_locked_oos": section(
                [row for row in rows if row["period"] in {"validation", "locked_oos"}]
            ),
            "locked_oos": section([row for row in rows if row["period"] == "locked_oos"]),
        },
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "common_buy_accuracy.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    with open(
        os.path.join(args.out, "common_buy_signals.csv"), "w", encoding="utf-8", newline=""
    ) as handle:
        fields = list(rows[0]) if rows else ["symbol", "date"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
