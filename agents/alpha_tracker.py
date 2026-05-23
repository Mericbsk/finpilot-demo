"""Alpha Tracker Agent — sembol bazında rolling win rate ve profit factor izler.

Her scanner döngüsünden sonra çalışır. Son N sinyalin sonucunu sembol
başına hesaplayarak hangi sembollerin iyi/kötü performans gösterdiğini
belirler. Eşik altındaki semboller için scanner score threshold önerisi üretir.

Input  : AgentContext.symbols  (boş olabilir — tüm kayıtlı semboller taranır)
         kwargs:
           rolling_window : int   (default: 10) — kaç sinyal geriye bakılır
           warn_threshold : float (default: 40.0) — bu win rate altı = WARN
           drop_threshold : float (default: 30.0) — bu win rate altı = DROP (threshold yükselt)

Output : AgentResult.data = {
    "symbols": {
        "AAPL": {
            "win_rate": 70.0,
            "profit_factor": 2.1,
            "avg_rr": 1.8,
            "total": 10,
            "wins": 7,
            "losses": 3,
            "status": "STRONG" | "OK" | "WARN" | "DROP",
            "recommended_threshold_boost": 0 | 5 | 10,
        },
        ...
    },
    "fleet_win_rate": 58.3,       # Tüm sembollerin ortalama win rate'i
    "underperformers": ["TSLA"],   # WARN veya DROP statüsündekiler
    "outperformers": ["NVDA"],     # STRONG statüsündekiler
    "summary": str,
    "evaluated_at": str,
}
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from agents.base import AgentContext, AgentResult, BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_ROLLING_WINDOW = 10
_DEFAULT_WARN_THRESHOLD = 40.0
_DEFAULT_DROP_THRESHOLD = 30.0

# Redis key — canlı score floor
_SCORE_FLOOR_KEY = "finpilot:alpha_score_floor"
_SCORE_FLOOR_TTL = 86400 * 7   # 7 gün
_mem_score_floor: int | None = None


def set_score_floor(value: int) -> None:
    """Alpha tracker çıktısındaki recommended_min_score'u kaydet.
    Scanner bu değeri okuyarak düşük composite_score'lu sinyalleri filtreler.
    """
    global _mem_score_floor
    _mem_score_floor = int(value)
    try:
        from core.kpi_tracker import _get_redis
        r = _get_redis()
        if r is not None:
            r.set(_SCORE_FLOOR_KEY, str(value), ex=_SCORE_FLOOR_TTL)
    except Exception:
        pass
    logger.info("AlphaTracker: score floor set → %d", value)


def get_score_floor() -> int | None:
    """Geçerli score floor'u döndür; hiç set edilmemişse None."""
    global _mem_score_floor
    if _mem_score_floor is not None:
        return _mem_score_floor
    try:
        from core.kpi_tracker import _get_redis
        r = _get_redis()
        if r is not None:
            raw = r.get(_SCORE_FLOOR_KEY)
            if raw:
                _mem_score_floor = int(raw)
                return _mem_score_floor
    except Exception:
        pass
    return None


# Score bucket edges — her aralık [low, high)
_SCORE_BUCKETS: list[tuple[int, int]] = [
    (0,  40),
    (40, 50),
    (50, 60),
    (60, 70),
    (70, 80),
    (80, 90),
    (90, 101),
]


def _bucket_label(low: int, high: int) -> str:
    return f"{low}-{min(high - 1, 100)}"


def _calc_score_buckets(resolved_signals: list[dict]) -> dict[str, Any]:
    """Tüm çözümlenmiş sinyalleri score aralıklarına göre grupla.

    Returns:
        {
            "40-49": {"win_rate": 55.0, "total": 20, "wins": 11, "avg_profit_pct": 1.8},
            ...
            "best_bucket": "70-79",
            "best_win_rate": 82.0,
            "recommended_min_score": 70,
        }
    """
    buckets: dict[str, dict[str, Any]] = {}
    for low, high in _SCORE_BUCKETS:
        label = _bucket_label(low, high)
        in_bucket = [
            s for s in resolved_signals
            if low <= (s.get("score") or 0) < high
        ]
        wins = [s for s in in_bucket if s.get("outcome") == "win"]
        losses = [s for s in in_bucket if s.get("outcome") == "loss"]
        if not in_bucket:
            continue
        win_rate = round(len(wins) / len(in_bucket) * 100, 1)
        avg_profit = round(
            sum(s.get("profit_pct") or 0.0 for s in wins) / len(wins), 2
        ) if wins else 0.0
        avg_loss = round(
            sum(abs(s.get("profit_pct") or 0.0) for s in losses) / len(losses), 2
        ) if losses else 0.0
        buckets[label] = {
            "score_range": [low, min(high - 1, 100)],
            "total": len(in_bucket),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "avg_win_pct": avg_profit,
            "avg_loss_pct": avg_loss,
        }

    if not buckets:
        return {"buckets": {}, "best_bucket": None, "best_win_rate": None, "recommended_min_score": None}

    # En yüksek win rate'li aralık (en az 3 sinyal şartıyla)
    qualifying = {k: v for k, v in buckets.items() if v["total"] >= 3}
    if qualifying:
        best_label = max(qualifying, key=lambda k: qualifying[k]["win_rate"])
        best_wr = qualifying[best_label]["win_rate"]
        recommended_min = qualifying[best_label]["score_range"][0]
    else:
        # Yeterli sinyal yoksa minimum score aralığını bul
        best_label = max(buckets, key=lambda k: buckets[k]["win_rate"])
        best_wr = buckets[best_label]["win_rate"]
        recommended_min = buckets[best_label]["score_range"][0]

    return {
        "buckets": buckets,
        "best_bucket": best_label,
        "best_win_rate": best_wr,
        "recommended_min_score": recommended_min,
    }


def _classify(win_rate: float, warn: float, drop: float) -> tuple[str, int]:
    """Sembol performansını sınıflandır.

    Returns:
        (status, recommended_threshold_boost)
        - STRONG  → win_rate >= 60  → boost 0  (eşiği düşürebilirsin)
        - OK      → 40 <= wr < 60   → boost 0
        - WARN    → drop <= wr < 40 → boost +5 (eşiği biraz yükselt)
        - DROP    → wr < drop       → boost +10 (bu sembolü filtrele)
    """
    if win_rate >= 60.0:
        return "STRONG", 0
    if win_rate >= warn:
        return "OK", 0
    if win_rate >= drop:
        return "WARN", 5
    return "DROP", 10


class AlphaTrackerAgent(BaseAgent):
    """Sembol başına rolling sinyal performansını hesaplar ve scanner önerisi üretir."""

    name = "alpha_tracker"

    def run(self, context: AgentContext, **kwargs: Any) -> AgentResult:  # noqa: D102
        import time

        t0 = time.perf_counter()
        rolling_window: int = int(kwargs.get("rolling_window", _DEFAULT_ROLLING_WINDOW))
        warn_threshold: float = float(kwargs.get("warn_threshold", _DEFAULT_WARN_THRESHOLD))
        drop_threshold: float = float(kwargs.get("drop_threshold", _DEFAULT_DROP_THRESHOLD))

        try:
            from core.kpi_tracker import _load_all_signals
        except ImportError as exc:
            return AgentResult(
                agent=self.name,
                success=False,
                error=f"kpi_tracker import failed: {exc}",
                duration_ms=(time.perf_counter() - t0) * 1000,
            )

        all_signals = _load_all_signals()

        # Sembol başına en yeni N sinyali grupla
        by_symbol: dict[str, list[dict]] = defaultdict(list)
        for sig in all_signals:
            sym = sig.get("symbol", "")
            if sym:
                by_symbol[sym].append(sig)

        # Eğer context.symbols verilmişse sadece onları değerlendir
        target_symbols = context.symbols if context.symbols else list(by_symbol.keys())

        results: dict[str, Any] = {}
        all_win_rates: list[float] = []
        underperformers: list[str] = []
        outperformers: list[str] = []

        for sym in target_symbols:
            signals = by_symbol.get(sym, [])
            # En yeni rolling_window kadar sinyal, sadece sonucu olan
            resolved = [s for s in signals if s.get("outcome") is not None]
            resolved = resolved[:rolling_window]

            if not resolved:
                results[sym] = {
                    "win_rate": None,
                    "profit_factor": None,
                    "avg_rr": None,
                    "total": 0,
                    "wins": 0,
                    "losses": 0,
                    "status": "NO_DATA",
                    "recommended_threshold_boost": 0,
                }
                continue

            wins = [s for s in resolved if s["outcome"] == "win"]
            losses = [s for s in resolved if s["outcome"] == "loss"]

            win_rate = round(len(wins) / len(resolved) * 100, 1)

            # Profit factor
            total_profit = sum(s.get("profit_pct", 0.0) or 0.0 for s in wins)
            total_loss = abs(sum(s.get("profit_pct", 0.0) or 0.0 for s in losses))
            profit_factor = (
                round(total_profit / total_loss, 2) if total_loss > 0 else 999.0
            )

            # Avg R:R
            rr_values = [s["rr"] for s in resolved if s.get("rr", 0) > 0]
            avg_rr = round(sum(rr_values) / len(rr_values), 2) if rr_values else 0.0

            status, boost = _classify(win_rate, warn_threshold, drop_threshold)

            results[sym] = {
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_rr": avg_rr,
                "total": len(resolved),
                "wins": len(wins),
                "losses": len(losses),
                "status": status,
                "recommended_threshold_boost": boost,
            }

            all_win_rates.append(win_rate)

            if status in ("WARN", "DROP"):
                underperformers.append(sym)
            elif status == "STRONG":
                outperformers.append(sym)

        fleet_win_rate = (
            round(sum(all_win_rates) / len(all_win_rates), 1) if all_win_rates else 0.0
        )

        # Score bucket analizi — tüm çözümlenmiş sinyaller üzerinden
        all_resolved = [s for s in all_signals if s.get("outcome") is not None]
        score_analysis = _calc_score_buckets(all_resolved)

        # İnsan okunur özet
        total_evaluated = len([v for v in results.values() if v["status"] != "NO_DATA"])
        summary_parts = [
            f"{total_evaluated} sembol değerlendirildi.",
            f"Filo win rate: %{fleet_win_rate}.",
        ]
        if outperformers:
            summary_parts.append(f"Güçlü: {', '.join(outperformers[:5])}.")
        if underperformers:
            summary_parts.append(
                f"Düşük performans ({len(underperformers)} sembol): "
                f"{', '.join(underperformers[:5])} — "
                "scanner eşiği artırılmalı."
            )
        if not underperformers and total_evaluated > 0:
            summary_parts.append("Tüm semboller kabul edilebilir performansta.")
        if score_analysis["best_bucket"]:
            summary_parts.append(
                f"En kazandıran puan aralığı: {score_analysis['best_bucket']} "
                f"(win rate %{score_analysis['best_win_rate']}, "
                f"önerilen min. puan: {score_analysis['recommended_min_score']})."
            )

        # Score floor'u otomatik kaydet — scanner bir sonraki taramada okur
        if score_analysis["recommended_min_score"] is not None:
            set_score_floor(score_analysis["recommended_min_score"])

        data = {
            "symbols": results,
            "fleet_win_rate": fleet_win_rate,
            "underperformers": underperformers,
            "outperformers": outperformers,
            "rolling_window": rolling_window,
            "score_analysis": score_analysis,
            "active_score_floor": score_analysis["recommended_min_score"],
            "summary": " ".join(summary_parts),
            "evaluated_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
        }

        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "AlphaTracker: %d sembols, fleet_wr=%.1f%%, under=%d, over=%d (%.0fms)",
            total_evaluated,
            fleet_win_rate,
            len(underperformers),
            len(outperformers),
            duration_ms,
        )

        return AgentResult(
            agent=self.name,
            success=True,
            data=data,
            duration_ms=duration_ms,
        )


# ---------------------------------------------------------------------------
# Convenience helpers — doğrudan import için
# ---------------------------------------------------------------------------


def get_symbol_win_rate(symbol: str, rolling_window: int = 10) -> float | None:
    """Tek sembolün rolling win rate'ini döndür (%); veri yoksa None."""
    try:
        from core.kpi_tracker import _load_all_signals
    except ImportError:
        return None

    signals = [s for s in _load_all_signals() if s.get("symbol") == symbol]
    resolved = [s for s in signals if s.get("outcome") is not None][:rolling_window]
    if not resolved:
        return None
    wins = sum(1 for s in resolved if s["outcome"] == "win")
    return round(wins / len(resolved) * 100, 1)


def get_threshold_boosts(
    warn_threshold: float = _DEFAULT_WARN_THRESHOLD,
    drop_threshold: float = _DEFAULT_DROP_THRESHOLD,
    rolling_window: int = _DEFAULT_ROLLING_WINDOW,
) -> dict[str, int]:
    """Tüm semboller için önerilen scanner threshold artış miktarlarını döndür.

    Scanner bu dict'i okuyarak düşük win rate'li sembollerde minimum score'u
    otomatik olarak yükseltebilir.

    Returns:
        {"TSLA": 10, "AMD": 5, "AAPL": 0, ...}
    """
    ctx = AgentContext()
    result = AlphaTrackerAgent().run(
        ctx,
        warn_threshold=warn_threshold,
        drop_threshold=drop_threshold,
        rolling_window=rolling_window,
    )
    if not result.success:
        return {}
    return {
        sym: info["recommended_threshold_boost"]
        for sym, info in result.data["symbols"].items()
        if info["status"] != "NO_DATA"
    }
