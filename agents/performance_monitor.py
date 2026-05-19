"""Performance Monitor Agent — gerçek zamanlı drawdown izleme ve WARN/STOP mekanizması.

Input  : AgentContext.symbols + optional kwargs:
           warn_drawdown_pct  : float (default: 10.0) — WARN eşiği
           stop_drawdown_pct  : float (default: 20.0) — STOP eşiği
           lookback_days      : int   (default: 30)   — değerlendirme penceresi
           portfolio_value    : float (default: None) — toplam portföy değeri
Process:
    1. Her sembol için yfinance'den son fiyat + lookback verisi çek
    2. Peak-to-current drawdown hesapla
    3. Eşiği geçenlere WARN veya STOP sinyali üret
    4. Portfolio geneli durum özeti çıkar
Output : AgentResult.data = {
    "symbols": dict[symbol, MonitorResult],
    "portfolio_status": "OK" | "WARN" | "STOP",
    "total_warnings": int,
    "total_stops": int,
    "summary": str,
    "checked_at": str,
}
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_WARN_PCT = 10.0
_DEFAULT_STOP_PCT = 20.0
_DEFAULT_LOOKBACK = 30


def _calc_drawdown(prices: list[float]) -> tuple[float, float]:
    """Peak-to-trough ve peak-to-current drawdown hesapla (%).
    Returns: (max_drawdown_pct, current_drawdown_pct)
    """
    if len(prices) < 2:
        return 0.0, 0.0

    peak = prices[0]
    max_dd = 0.0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak * 100
        if dd > max_dd:
            max_dd = dd

    current_peak = max(prices)
    current_dd = (current_peak - prices[-1]) / current_peak * 100 if current_peak > 0 else 0.0

    return round(max_dd, 2), round(current_dd, 2)


class PerformanceMonitorAgent(BaseAgent):
    """Monitor portfolio symbols for drawdown breaches and emit WARN/STOP signals."""

    name = "performance_monitor"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()
        warn_pct: float = float(kwargs.get("warn_drawdown_pct", _DEFAULT_WARN_PCT))
        stop_pct: float = float(kwargs.get("stop_drawdown_pct", _DEFAULT_STOP_PCT))
        lookback: int = int(kwargs.get("lookback_days", _DEFAULT_LOOKBACK))

        try:
            import yfinance as yf
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"yfinance unavailable: {exc}")

        symbol_results: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        total_warns = 0
        total_stops = 0

        for sym in context.symbols:
            try:
                df = yf.download(sym, period=f"{lookback + 5}d", progress=False, auto_adjust=True)
                if df.empty or len(df) < 5:
                    errors.append(f"{sym}: yetersiz veri ({len(df)} bar)")
                    continue

                df = df.tail(lookback)
                closes = df["Close"].squeeze().tolist()
                if not closes:
                    continue

                max_dd, current_dd = _calc_drawdown(closes)

                # Durum tespiti
                if current_dd >= stop_pct:
                    status = "STOP"
                    total_stops += 1
                elif current_dd >= warn_pct:
                    status = "WARN"
                    total_warns += 1
                else:
                    status = "OK"

                # Son 5 gün performansı
                perf_5d = (closes[-1] / closes[-5] - 1) * 100 if len(closes) >= 5 else 0.0

                # Volatilite (günlük std)
                rets = [
                    (closes[i] - closes[i - 1]) / closes[i - 1] * 100 for i in range(1, len(closes))
                ]
                import statistics

                daily_vol = statistics.stdev(rets) if len(rets) > 1 else 0.0

                symbol_results[sym] = {
                    "symbol": sym,
                    "status": status,
                    "current_drawdown_pct": round(current_dd, 2),
                    "max_drawdown_pct": max_dd,
                    "last_price": round(float(closes[-1]), 4),
                    "period_high": round(float(max(closes)), 4),
                    "perf_5d_pct": round(perf_5d, 2),
                    "daily_vol_pct": round(daily_vol, 2),
                    "warn_threshold_pct": warn_pct,
                    "stop_threshold_pct": stop_pct,
                    "action": _get_action(status),
                }
                logger.info("PerfMonitor: %s → %s (dd=%.1f%%)", sym, status, current_dd)

            except Exception as exc:
                logger.warning("PerfMonitor: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")

        if not symbol_results and errors:
            return AgentResult(agent=self.name, success=False, error="; ".join(errors))

        # Portfolio geneli durum
        if total_stops > 0:
            portfolio_status = "STOP"
        elif total_warns > 0:
            portfolio_status = "WARN"
        else:
            portfolio_status = "OK"

        ok_cnt = sum(1 for v in symbol_results.values() if v["status"] == "OK")
        summary = (
            f"{len(symbol_results)} sembol izlendi — "
            f"OK: {ok_cnt}, WARN: {total_warns}, STOP: {total_stops}. "
            f"Portfolio durumu: {portfolio_status}."
        )

        duration = (time.perf_counter() - t0) * 1000
        return AgentResult(
            agent=self.name,
            success=True,
            data={
                "symbols": symbol_results,
                "portfolio_status": portfolio_status,
                "total_warnings": total_warns,
                "total_stops": total_stops,
                "ok_count": ok_cnt,
                "summary": summary,
                "errors": errors,
                "checked_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
            },
            duration_ms=duration,
        )


def _get_action(status: str) -> str:
    if status == "STOP":
        return "Pozisyonu kapat. Yüksek kayıp riski."
    if status == "WARN":
        return "Pozisyonu küçült veya stop-loss'u sıkılaştır."
    return "Pozisyonu izlemeye devam et."
