"""Market Intelligence Agent — piyasa rejim tespiti ve makro analiz.

Input  : AgentContext.symbols + optional kwargs:
           lookback_days : int (default: 60)  — volatilite/trend penceresi
Process:
    1. Her sembol için yfinance'den günlük OHLCV çek
    2. Volatilite rejimi hesapla (low / medium / high)
    3. Trend rejimi tespit et (bull / bear / sideways)
    4. Piyasa geneli özet üret
    5. İsteğe bağlı LLM yorumu ekle
Output : AgentResult.data = {
    "symbols": dict[symbol, RegimaInfo],
    "market_summary": str,
    "dominant_regime": str,  # "bull" | "bear" | "sideways" | "mixed"
    "analyzed_at": str,
}
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_LOOKBACK = 60  # gün


def _classify_trend(returns_pct: float, slope_pct: float) -> str:
    """Kümülatif getiri ve lineer regresyon eğimine göre trend rejimi."""
    if returns_pct > 5 and slope_pct > 0:
        return "bull"
    if returns_pct < -5 and slope_pct < 0:
        return "bear"
    return "sideways"


def _classify_volatility(ann_vol: float) -> str:
    """Yıllıklaştırılmış volatiliteye göre rejim."""
    if ann_vol < 20:
        return "low"
    if ann_vol < 40:
        return "medium"
    return "high"


def _calc_slope_pct(closes: list[float]) -> float:
    """Basit lineer regresyon eğimini % cinsinden döndür."""
    n = len(closes)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(closes) / n
    num = sum((i - x_mean) * (closes[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0.0
    # Günlük slope'u % olarak (ilk fiyata göre normalise)
    return (slope / closes[0]) * 100 if closes[0] else 0.0


class MarketIntelligenceAgent(BaseAgent):
    """Detect market regime (trend + volatility) for a list of symbols."""

    name = "market_intel"

    def run(self, context: AgentContext, **kwargs: object) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()
        lookback: int = int(kwargs.get("lookback_days", _DEFAULT_LOOKBACK))
        use_llm: bool = bool(kwargs.get("use_llm", False))

        try:
            import yfinance as yf
        except ImportError as exc:
            return AgentResult(agent=self.name, success=False, error=f"yfinance unavailable: {exc}")

        symbol_data: dict[str, dict[str, Any]] = {}
        errors: list[str] = []

        for sym in context.symbols:
            try:
                df = yf.download(sym, period=f"{lookback + 10}d", progress=False, auto_adjust=True)
                if df.empty or len(df) < 20:
                    errors.append(f"{sym}: insufficient data ({len(df)} bars)")
                    continue

                df = df.tail(lookback)
                closes = df["Close"].squeeze().tolist()
                if not closes:
                    continue

                # Daily returns
                rets = [
                    (closes[i] - closes[i - 1]) / closes[i - 1] * 100 for i in range(1, len(closes))
                ]

                # Metrics
                cum_return = (closes[-1] / closes[0] - 1) * 100
                slope_pct = _calc_slope_pct(closes)
                import statistics

                daily_vol = statistics.stdev(rets) if len(rets) > 1 else 0.0
                ann_vol = daily_vol * (252**0.5)

                trend = _classify_trend(cum_return, slope_pct)
                volatility = _classify_volatility(ann_vol)

                # RSI(14) — lightweight, no ta-lib needed
                gains = [r for r in rets if r > 0]
                losses = [-r for r in rets if r < 0]
                avg_gain = sum(gains[-14:]) / 14 if gains else 0
                avg_loss = sum(losses[-14:]) / 14 if losses else 0.001
                rsi = 100 - (100 / (1 + avg_gain / avg_loss))

                # 20-day SMA gap
                sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
                sma_gap_pct = (closes[-1] / sma20 - 1) * 100

                symbol_data[sym] = {
                    "symbol": sym,
                    "trend": trend,
                    "volatility": volatility,
                    "cum_return_pct": round(cum_return, 2),
                    "ann_vol_pct": round(ann_vol, 2),
                    "rsi_14": round(rsi, 1),
                    "sma20_gap_pct": round(sma_gap_pct, 2),
                    "last_price": round(float(closes[-1]), 4),
                    "lookback_days": lookback,
                    "score": _regime_score(trend, volatility, rsi, sma_gap_pct),
                }
                logger.info(
                    "MarketIntel: %s → trend=%s vol=%s rsi=%.1f", sym, trend, volatility, rsi
                )

            except Exception as exc:
                logger.warning("MarketIntel: %s failed: %s", sym, exc)
                errors.append(f"{sym}: {exc}")

        if not symbol_data and errors:
            return AgentResult(agent=self.name, success=False, error="; ".join(errors))

        # Dominant regime
        trends = [v["trend"] for v in symbol_data.values()]
        dominant = max(set(trends), key=trends.count) if trends else "mixed"
        if len(set(trends)) > 1 and trends.count(dominant) < len(trends) * 0.6:
            dominant = "mixed"

        # Market summary text
        bull_cnt = trends.count("bull")
        bear_cnt = trends.count("bear")
        side_cnt = trends.count("sideways")
        avg_vol = (
            sum(v["ann_vol_pct"] for v in symbol_data.values()) / len(symbol_data)
            if symbol_data
            else 0
        )
        summary = (
            f"{len(symbol_data)} sembol analiz edildi — "
            f"Bull: {bull_cnt}, Bear: {bear_cnt}, Yatay: {side_cnt}. "
            f"Ort. yıllık volatilite: %{avg_vol:.1f}. "
            f"Dominant rejim: {dominant.upper()}."
        )

        # Optional LLM commentary
        llm_comment: str | None = None
        if use_llm and symbol_data:
            try:
                from llm import get_router
                from llm.base import LLMMessage, LLMRole

                router = get_router()
                prompt = (
                    f"Piyasa durumu özeti:\n{summary}\n\n"
                    f"Sembol detayları:\n"
                    + "\n".join(
                        f"  {sym}: trend={d['trend']}, vol={d['volatility']}, "
                        f"RSI={d['rsi_14']}, getiri=%{d['cum_return_pct']}"
                        for sym, d in list(symbol_data.items())[:5]
                    )
                    + "\n\nBu piyasa koşullarını kısaca yorumla ve önerilen strateji yaklaşımını belirt."
                )
                resp = router.generate_messages(
                    messages=[
                        LLMMessage(
                            role=LLMRole.SYSTEM,
                            content="Sen kıdemli bir piyasa stratejistisin. Kısa ve net cevaplar ver.",
                        ),
                        LLMMessage(role=LLMRole.USER, content=prompt),
                    ],
                    temperature=0.3,
                    max_tokens=400,
                )
                llm_comment = resp.content
            except Exception as exc:
                logger.warning("MarketIntel LLM failed: %s", exc)

        duration = (time.perf_counter() - t0) * 1000
        return AgentResult(
            agent=self.name,
            success=True,
            data={
                "symbols": symbol_data,
                "market_summary": summary,
                "dominant_regime": dominant,
                "bull_count": bull_cnt,
                "bear_count": bear_cnt,
                "sideways_count": side_cnt,
                "avg_ann_vol_pct": round(avg_vol, 2),
                "llm_comment": llm_comment,
                "analyzed_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
                "errors": errors,
            },
            duration_ms=duration,
        )


def _regime_score(trend: str, volatility: str, rsi: float, sma_gap: float) -> int:
    """0–100 arası rejim kalite skoru. Yüksek = daha iyi giriş ortamı."""
    score = 0
    # Trend
    if trend == "bull":
        score += 40
    elif trend == "sideways":
        score += 20
    # Volatility (medium tercih edilir — çok düşük = hareket yok, çok yüksek = risk)
    if volatility == "medium":
        score += 25
    elif volatility == "low":
        score += 15
    # RSI (30–70 arası ideal)
    if 35 <= rsi <= 65:
        score += 20
    elif 25 <= rsi < 35 or 65 < rsi <= 75:
        score += 10
    # SMA gap (fiyat SMA'nın hafif üzerinde ideal)
    if 0 < sma_gap <= 5:
        score += 15
    elif -2 <= sma_gap <= 0:
        score += 8
    return min(score, 100)
