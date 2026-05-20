"""Offline evaluation harness for FinPilot multi-agent system.

Usage:
    python -m tests.eval.eval_harness --symbols AAPL MSFT --output reports/eval.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal accuracy evaluation
# ---------------------------------------------------------------------------


async def eval_signal_accuracy(symbols: list[str]) -> dict[str, Any]:
    """Evaluate direction accuracy of CEO scan signals vs KPI records."""
    try:
        from core.kpi_tracker import KPITracker

        tracker = KPITracker()
        metrics = await tracker.get_metrics()

        direction_hits = 0
        direction_total = 0
        for sym in symbols:
            sym_metrics = metrics.get(sym, {})
            signals = sym_metrics.get("signals", [])
            for sig in signals:
                if "direction" in sig and "actual" in sig:
                    direction_total += 1
                    if sig["direction"] == sig["actual"]:
                        direction_hits += 1

        accuracy = direction_hits / direction_total if direction_total else None
        return {
            "metric": "signal_direction_accuracy",
            "symbols_evaluated": symbols,
            "hits": direction_hits,
            "total": direction_total,
            "accuracy": accuracy,
            "status": "ok",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("signal_accuracy eval failed: %s", exc)
        return {"metric": "signal_direction_accuracy", "status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Backtest quality evaluation
# ---------------------------------------------------------------------------


async def eval_backtest_quality(symbols: list[str]) -> dict[str, Any]:
    """Check BacktestAgent win_rate and profit_factor across recent runs."""
    try:
        from core.agent_state import get_agent_result

        results = []
        for sym in symbols:
            data = await get_agent_result("backtest", [sym])
            if data:
                results.append(
                    {
                        "symbol": sym,
                        "win_rate": data.get("win_rate"),
                        "profit_factor": data.get("profit_factor"),
                    }
                )

        valid = [r for r in results if r["win_rate"] is not None]
        avg_win_rate = sum(r["win_rate"] for r in valid) / len(valid) if valid else None
        avg_pf = (
            sum(r["profit_factor"] for r in valid if r["profit_factor"] is not None)
            / len([r for r in valid if r["profit_factor"] is not None])
            if valid
            else None
        )

        return {
            "metric": "backtest_quality",
            "symbols_evaluated": symbols,
            "results": results,
            "avg_win_rate": avg_win_rate,
            "avg_profit_factor": avg_pf,
            "threshold_win_rate": 0.50,
            "threshold_profit_factor": 1.0,
            "passes_win_rate": avg_win_rate >= 0.50 if avg_win_rate is not None else None,
            "passes_profit_factor": avg_pf >= 1.0 if avg_pf is not None else None,
            "status": "ok",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("backtest_quality eval failed: %s", exc)
        return {"metric": "backtest_quality", "status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Data quality evaluation
# ---------------------------------------------------------------------------


async def eval_data_quality(symbols: list[str]) -> dict[str, Any]:
    """Measure DataQualityAgent pass rate across the given symbols."""
    try:
        from core.agent_state import get_agent_result

        passed = 0
        total = 0
        symbol_details = []
        for sym in symbols:
            data = await get_agent_result("data_quality", [sym])
            if data:
                total += 1
                ok = data.get("passed", False)
                if ok:
                    passed += 1
                symbol_details.append(
                    {
                        "symbol": sym,
                        "passed": ok,
                        "quality_score": data.get("quality_score"),
                        "issues": data.get("issues", []),
                    }
                )

        pass_rate = passed / total if total else None
        return {
            "metric": "data_quality_pass_rate",
            "symbols_evaluated": symbols,
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate,
            "threshold": 0.80,
            "passes_threshold": pass_rate >= 0.80 if pass_rate is not None else None,
            "details": symbol_details,
            "status": "ok",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("data_quality eval failed: %s", exc)
        return {"metric": "data_quality_pass_rate", "status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# KPI summary evaluation
# ---------------------------------------------------------------------------


async def eval_kpi_summary(symbols: list[str]) -> dict[str, Any]:
    """Aggregate KPI stats from the KPITracker."""
    try:
        from core.kpi_tracker import KPITracker

        tracker = KPITracker()
        summary = await tracker.get_summary()
        return {
            "metric": "kpi_summary",
            "symbols": symbols,
            "summary": summary,
            "status": "ok",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("kpi_summary eval failed: %s", exc)
        return {"metric": "kpi_summary", "status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------


async def run_eval(
    symbols: list[str],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Run all eval checks and return a combined report dict."""
    signal_acc, backtest_q, data_q, kpi_sum = await asyncio.gather(
        eval_signal_accuracy(symbols),
        eval_backtest_quality(symbols),
        eval_data_quality(symbols),
        eval_kpi_summary(symbols),
    )

    report = {
        "eval_timestamp": datetime.now(tz=UTC).isoformat(),
        "symbols": symbols,
        "results": {
            "signal_accuracy": signal_acc,
            "backtest_quality": backtest_q,
            "data_quality": data_q,
            "kpi_summary": kpi_sum,
        },
        "overall_pass": all(
            r.get("status") == "ok" and r.get("passes_threshold", True) is not False
            for r in [signal_acc, backtest_q, data_q]
        ),
    }

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        logger.info("Eval report written to %s", output_path)

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="FinPilot offline eval harness")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL"],
        help="Symbols to evaluate (default: AAPL MSFT GOOGL)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write JSON report (optional)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    report = asyncio.run(run_eval(args.symbols, args.output))
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
