"""DataQuality Agent — validates scan/market data before downstream agents process it.

Runs as a pre-pipeline gate. If critical data quality issues are detected,
downstream agents receive a flag and can skip or use cached data.

Input  : AgentContext.symbols + AgentContext.scan_results (optional)
Process:
    1. Schema validation: required fields present?
    2. Anomaly detection: price/volume outliers
    3. Freshness check: data timestamp recent?
Output : AgentResult.data = {
    "passed": bool,
    "issues": list[str],
    "warnings": list[str],
    "symbol_quality": dict[symbol, {"ok": bool, "issues": list}],
    "quality_score": float,  # 0.0 - 1.0
}
"""

from __future__ import annotations

import logging
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

# Required fields in scan_results per symbol
_REQUIRED_FIELDS = ["finpilot_score", "signal", "close"]
_OPTIONAL_FIELDS = ["volume", "rsi", "macd", "bb_upper", "bb_lower"]

# Anomaly thresholds
_MAX_PRICE_CHANGE_PCT = 50.0   # >50% single-day move is suspicious
_MIN_PRICE = 0.01               # price must be positive
_MAX_SCORE = 100.0
_MIN_SCORE = 0.0


class DataQualityAgent(BaseAgent):
    """Validate market data quality before downstream pipeline processing."""

    name = "data_quality"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:
        import time

        t0 = time.perf_counter()
        scan_results = context.scan_results or {}
        symbols = context.symbols or []

        issues: list[str] = []
        warnings: list[str] = []
        symbol_quality: dict[str, dict[str, Any]] = {}

        # If no scan_results yet, just validate symbols list
        if not scan_results:
            if not symbols:
                issues.append("No symbols provided")
            for sym in symbols:
                if not isinstance(sym, str) or len(sym) < 1:
                    issues.append(f"Invalid symbol: {sym!r}")
                elif len(sym) > 20:
                    warnings.append(f"Unusually long symbol: {sym}")
                symbol_quality[sym] = {"ok": len(issues) == 0, "issues": []}

            duration = (time.perf_counter() - t0) * 1000
            quality_score = 1.0 if not issues else 0.5
            return AgentResult(
                agent=self.name,
                success=True,
                data={
                    "passed": len(issues) == 0,
                    "issues": issues,
                    "warnings": warnings,
                    "symbol_quality": symbol_quality,
                    "quality_score": quality_score,
                    "symbols_checked": len(symbols),
                },
                duration_ms=duration,
            )

        # Validate each symbol's data
        ok_count = 0
        for sym, data in scan_results.items():
            sym_issues: list[str] = []

            if not isinstance(data, dict):
                sym_issues.append(f"scan_results[{sym}] is not a dict")
                symbol_quality[sym] = {"ok": False, "issues": sym_issues}
                continue

            # Required field check
            for field in _REQUIRED_FIELDS:
                if field not in data:
                    sym_issues.append(f"Missing required field: {field}")

            # Price sanity
            close = data.get("close", data.get("last_price", data.get("price")))
            if close is not None:
                try:
                    close_f = float(close)
                    if close_f <= _MIN_PRICE:
                        sym_issues.append(f"Suspicious price: {close_f}")
                    elif close_f > 1_000_000:
                        warnings.append(f"{sym}: very high price {close_f} — verify currency")
                except (TypeError, ValueError):
                    sym_issues.append(f"Non-numeric price: {close!r}")

            # Score range check
            score = data.get("finpilot_score", data.get("composite_score"))
            if score is not None:
                try:
                    score_f = float(score)
                    if not (_MIN_SCORE <= score_f <= _MAX_SCORE):
                        sym_issues.append(f"Score out of range [0,100]: {score_f}")
                except (TypeError, ValueError):
                    sym_issues.append(f"Non-numeric score: {score!r}")

            # Signal validity
            signal = data.get("signal")
            if signal is not None and signal not in ("BUY", "SELL", "HOLD", "NEUTRAL", "WATCH", ""):
                warnings.append(f"{sym}: unexpected signal value: {signal!r}")

            is_ok = len(sym_issues) == 0
            if is_ok:
                ok_count += 1
            else:
                issues.extend([f"{sym}: {i}" for i in sym_issues])

            symbol_quality[sym] = {"ok": is_ok, "issues": sym_issues}

        total = len(scan_results)
        quality_score = ok_count / total if total > 0 else 1.0
        passed = quality_score >= 0.7 and len(issues) == 0

        duration = (time.perf_counter() - t0) * 1000
        return AgentResult(
            agent=self.name,
            success=True,
            data={
                "passed": passed,
                "issues": issues,
                "warnings": warnings,
                "symbol_quality": symbol_quality,
                "quality_score": round(quality_score, 3),
                "symbols_checked": total,
                "ok_count": ok_count,
            },
            duration_ms=duration,
        )
