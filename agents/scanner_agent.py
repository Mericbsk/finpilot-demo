"""Scanner Agent — wraps evaluate_symbols_parallel + DRL unified score.

Input  : AgentContext.symbols (list of ticker strings)
Process: evaluate_symbols_parallel → DRL cache overlay → finpilot_score
Output : AgentResult.data = dict[symbol, scan_row]
"""

from __future__ import annotations

import json
import logging

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class ScannerAgent(BaseAgent):
    """Run the FinPilot technical scanner on a batch of symbols.

    Wraps the existing ``evaluate_symbols_parallel`` function and
    overlays the unified FinPilot Score (scanner × DRL agreement).
    """

    name = "scanner"

    def run(self, context: AgentContext, kelly_fraction: float = 0.5) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()
        try:
            from scanner import evaluate_symbols_parallel
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"Scanner unavailable: {exc}")

        try:
            raw_results: list[dict] = evaluate_symbols_parallel(
                symbols=context.symbols,
                kelly_fraction=kelly_fraction,
            )
        except Exception as exc:
            logger.exception("ScannerAgent: evaluate_symbols_parallel failed")
            return AgentResult(
                agent=self.name,
                success=False,
                error=str(exc),
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        # Load DRL cache for finpilot_score overlay
        drl_cache, drl_valid = _load_drl_cache()

        try:
            from scanner.finpilot_score import compute_finpilot_score

            fps_available = True
        except ImportError:
            fps_available = False

        out: dict = {}
        for r in raw_results:
            sym: str | None = r.get("symbol") or r.get("ticker")
            if not sym:
                continue

            if fps_available:
                drl_entry = drl_cache.get(sym, {}) if drl_valid else {}
                r["finpilot_score"] = compute_finpilot_score(
                    scanner_composite=int(r.get("composite_score") or 0),
                    scanner_signal="BUY" if r.get("direction") else "SELL",
                    drl_signal=drl_entry.get("signal"),
                    drl_confidence=drl_entry.get("confidence"),
                )

            out[sym] = r

        duration = (time.perf_counter() - t0) * 1000
        logger.info("ScannerAgent: %d symbols in %.0fms", len(out), duration)
        return AgentResult(agent=self.name, success=True, data=out, duration_ms=duration)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_drl_cache() -> tuple[dict, bool]:
    """Load DRL inference cache, same logic as scan.py helper."""
    try:
        from routers.inference import _INFERENCE_PATH, _check_drl_cache

        if _INFERENCE_PATH.exists():
            cache = json.loads(_INFERENCE_PATH.read_text(encoding="utf-8"))
            valid = _check_drl_cache(cache).get("valid", False)
            return cache, valid
    except Exception as exc:
        logger.debug("ScannerAgent: DRL cache load skipped: %s", exc)
    return {}, False
