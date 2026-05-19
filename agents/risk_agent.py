"""Risk Agent — ATR-based risk management for scanned symbols.

Input  : AgentContext.symbols + AgentContext.scan_results (scanner rows)
Process: calculate_risk_management(price, atr, momentum) per symbol
Output : AgentResult.data = dict[symbol, risk_params_dict]

Wraps the existing ``scanner.risk_engine.calculate_risk_management`` function
which was extracted during Sprint 5 T3.
"""

from __future__ import annotations

import logging

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Calculate ATR-based stop-loss and take-profit parameters.

    Only processes symbols that have a valid price in scan_results.
    Symbols without price data are silently skipped (no error raised).
    """

    name = "risk"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()
        try:
            from scanner.risk_engine import calculate_risk_management
        except ImportError as exc:
            return AgentResult(
                agent=self.name, success=False, error=f"risk_engine unavailable: {exc}"
            )

        risk_out: dict = {}
        for sym in context.symbols:
            row = context.scan_results.get(sym, {})
            price = float(row.get("price") or 0)
            if price <= 0:
                logger.debug("RiskAgent: %s skipped — no valid price", sym)
                continue

            # ATR fallback: 2% of price when not available
            atr = float(row.get("atr") or price * 0.02)
            momentum_score = float(row.get("momentum_ratio") or 0.5)

            try:
                params = calculate_risk_management(price, atr, momentum_score)
                risk_out[sym] = params
            except Exception as exc:
                logger.warning("RiskAgent: %s risk calc failed: %s", sym, exc)

        duration = (time.perf_counter() - t0) * 1000
        logger.info("RiskAgent: %d symbols in %.0fms", len(risk_out), duration)
        return AgentResult(agent=self.name, success=True, data=risk_out, duration_ms=duration)
