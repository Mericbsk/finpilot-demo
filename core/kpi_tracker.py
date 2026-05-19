"""FinPilot KPI Tracker — agent sinyal performansını izler ve KPI hesaplar.

Her tur sonunda PerformanceMonitorAgent veya Scheduler bu modüle sinyal
kaydeder.  Redis varsa kalıcı, yoksa in-memory çalışır.

Tracked KPIs:
  - win_rate        : Doğru sinyal oranı (%)
  - profit_factor   : Kazanç / Kayıp toplamı
  - avg_rr          : Ortalama Risk/Reward
  - total_signals   : Toplam sinyal sayısı
  - total_wins      : Kazanan sinyal sayısı
  - cycle_scores    : Son N cycle'ın self-evaluation skoru

Usage::

    from core.kpi_tracker import record_signal, record_outcome, get_kpis, self_evaluate

    # Sinyal kaydı (scan sırasında)
    record_signal("THYAO.IS", "BUY", price=250.5, score=72, cycle=5)

    # Sonuç kaydı (drawdown monitor veya ertesi gün)
    record_outcome("THYAO.IS", cycle=5, profit_pct=3.2)

    # Mevcut KPI özeti
    kpis = get_kpis()

    # Otonom self-evaluation (cycle sonunda)
    report = self_evaluate(cycle_results)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis helpers (graceful fallback to in-memory)
# ---------------------------------------------------------------------------

_redis_client = None
_redis_unavailable = False

# In-memory fallback store
_mem_signals: list[dict] = []
_mem_kpis: dict[str, Any] = {
    "win_rate": 0.0,
    "profit_factor": 0.0,
    "avg_rr": 0.0,
    "total_signals": 0,
    "total_wins": 0,
    "total_losses": 0,
    "total_profit_pct": 0.0,
    "total_loss_pct": 0.0,
    "last_updated": None,
}
_mem_cycle_scores: list[dict] = []

SIGNALS_KEY = "finpilot:kpi_signals"
KPI_KEY = "finpilot:kpi_summary"
CYCLE_SCORES_KEY = "finpilot:kpi_cycle_scores"
MAX_SIGNALS = 500
MAX_CYCLE_SCORES = 100


def _get_redis():
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis  # type: ignore

        from core.config import get_settings

        url = get_settings().redis_url
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:
        logger.debug("KPI tracker: Redis unavailable (%s) — using in-memory", exc)
        _redis_unavailable = True
        return None


# ---------------------------------------------------------------------------
# Signal recording
# ---------------------------------------------------------------------------


def record_signal(
    symbol: str,
    direction: str,  # "BUY" | "SELL"
    price: float,
    score: float = 0.0,
    rr: float = 0.0,  # risk/reward ratio
    cycle: int = 0,
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
) -> None:
    """Record a new trading signal. Outcome can be updated later via record_outcome()."""
    signal: dict[str, Any] = {
        "id": f"{symbol}_{cycle}_{int(time.time())}",
        "symbol": symbol,
        "direction": direction,
        "price": round(price, 4),
        "score": round(score, 2),
        "rr": round(rr, 2),
        "stop_loss": round(stop_loss, 4),
        "take_profit": round(take_profit, 4),
        "cycle": cycle,
        "ts": int(time.time() * 1000),
        "outcome": None,  # filled by record_outcome()
        "profit_pct": None,
    }

    r = _get_redis()
    if r is not None:
        try:
            pipe = r.pipeline()
            pipe.lpush(SIGNALS_KEY, json.dumps(signal))
            pipe.ltrim(SIGNALS_KEY, 0, MAX_SIGNALS - 1)
            pipe.execute()
            return
        except Exception as exc:
            logger.debug("KPI record_signal Redis error: %s", exc)

    _mem_signals.insert(0, signal)
    if len(_mem_signals) > MAX_SIGNALS:
        _mem_signals.pop()


def record_outcome(
    symbol: str,
    cycle: int,
    profit_pct: float,  # positive = win, negative = loss
) -> None:
    """Update the outcome for a previously recorded signal and recompute KPIs."""
    won = profit_pct > 0

    r = _get_redis()
    if r is not None:
        try:
            raw = r.lrange(SIGNALS_KEY, 0, MAX_SIGNALS - 1)
            updated = False
            new_list = []
            for item in raw:
                sig = json.loads(item)
                if sig["symbol"] == symbol and sig["cycle"] == cycle and sig["outcome"] is None:
                    sig["outcome"] = "win" if won else "loss"
                    sig["profit_pct"] = round(profit_pct, 4)
                    updated = True
                new_list.append(json.dumps(sig))
            if updated:
                pipe = r.pipeline()
                pipe.delete(SIGNALS_KEY)
                for item in new_list:
                    pipe.rpush(SIGNALS_KEY, item)
                pipe.execute()
        except Exception as exc:
            logger.debug("KPI record_outcome Redis error: %s", exc)
    else:
        for sig in _mem_signals:
            if sig["symbol"] == symbol and sig["cycle"] == cycle and sig["outcome"] is None:
                sig["outcome"] = "win" if won else "loss"
                sig["profit_pct"] = round(profit_pct, 4)
                break

    _recompute_kpis()


def _recompute_kpis() -> dict[str, Any]:
    """Rebuild the KPI summary from all resolved signals."""
    global _mem_kpis

    signals = _load_all_signals()
    resolved = [s for s in signals if s.get("outcome") is not None]

    if not resolved:
        return _mem_kpis

    wins = [s for s in resolved if s["outcome"] == "win"]
    losses = [s for s in resolved if s["outcome"] == "loss"]

    total_profit = sum(s["profit_pct"] for s in wins if s.get("profit_pct"))
    total_loss = abs(sum(s["profit_pct"] for s in losses if s.get("profit_pct")))
    profit_factor = (total_profit / total_loss) if total_loss > 0 else float("inf")

    rr_values = [s["rr"] for s in resolved if s.get("rr", 0) > 0]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0

    kpis: dict[str, Any] = {
        "win_rate": round(len(wins) / len(resolved) * 100, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999.0,
        "avg_rr": round(avg_rr, 2),
        "total_signals": len(signals),
        "resolved_signals": len(resolved),
        "total_wins": len(wins),
        "total_losses": len(losses),
        "total_profit_pct": round(total_profit, 2),
        "total_loss_pct": round(total_loss, 2),
        "last_updated": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }

    r = _get_redis()
    if r is not None:
        try:
            r.set(KPI_KEY, json.dumps(kpis), ex=86400)
        except Exception:
            pass
    _mem_kpis = kpis
    return kpis


def _load_all_signals() -> list[dict]:
    r = _get_redis()
    if r is not None:
        try:
            raw = r.lrange(SIGNALS_KEY, 0, MAX_SIGNALS - 1)
            return [json.loads(item) for item in raw]
        except Exception:
            pass
    return _mem_signals[:]


# ---------------------------------------------------------------------------
# KPI retrieval
# ---------------------------------------------------------------------------


def get_kpis() -> dict[str, Any]:
    """Return the current KPI summary dict."""
    r = _get_redis()
    if r is not None:
        try:
            raw = r.get(KPI_KEY)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    if _mem_kpis["last_updated"] is None:
        _recompute_kpis()
    return _mem_kpis


def get_recent_signals(limit: int = 20) -> list[dict]:
    """Return the most recent signals (newest first)."""
    signals = _load_all_signals()
    return signals[:limit]


# ---------------------------------------------------------------------------
# Self-evaluation
# ---------------------------------------------------------------------------


def self_evaluate(cycle_results: dict[str, Any]) -> dict[str, Any]:
    """Analyze a completed agent cycle and produce a self-evaluation score (0–100).

    Scoring rubric:
      - 30 pts  KPI health (win_rate >= 55 → full; 40-55 → partial)
      - 25 pts  Errors     (0 errors → full; each error −5pts)
      - 25 pts  Coverage   (all 4 cycle steps successful)
      - 20 pts  Momentum   (win_rate trend over last 3 cycles)
    """
    kpis = get_kpis()
    errors: list[str] = cycle_results.get("errors", [])

    # 1. KPI health
    win_rate = kpis.get("win_rate", 0.0)
    if win_rate >= 55:
        kpi_score = 30
    elif win_rate >= 40:
        kpi_score = 15
    else:
        kpi_score = 5

    # 2. Error penalty
    error_score = max(0, 25 - len(errors) * 5)

    # 3. Coverage
    expected_steps = {"market_intel", "research", "backtest", "monitor"}
    done_steps = {k for k in expected_steps if cycle_results.get(k) is not None}
    coverage_score = round(len(done_steps) / len(expected_steps) * 25)

    # 4. Trend momentum
    scores_hist = get_cycle_scores(n=3)
    if len(scores_hist) >= 2:
        prev_scores = [s["score"] for s in scores_hist]
        trend = prev_scores[0] - prev_scores[-1]
        momentum_score = 20 if trend >= 0 else max(0, 20 + trend)
    else:
        momentum_score = 10  # neutral for first cycles

    total = kpi_score + error_score + coverage_score + int(momentum_score)
    total = min(100, max(0, total))

    recommendations: list[str] = []
    if win_rate < 50:
        recommendations.append(
            "Win rate düşük — strateji parametrelerini optimize et (Strategy Optimizer çalıştır)"
        )
    if len(errors) > 2:
        recommendations.append(f"{len(errors)} hata tespit edildi — veri kaynaklarını kontrol et")
    if len(done_steps) < len(expected_steps):
        missing = expected_steps - done_steps
        recommendations.append(
            f"Eksik adımlar: {', '.join(missing)} — agent bağlantılarını kontrol et"
        )
    if total >= 80:
        recommendations.append("Sistem iyi durumda — mevcut stratejiyi koru")

    evaluation = {
        "score": total,
        "grade": "A" if total >= 80 else "B" if total >= 65 else "C" if total >= 50 else "D",
        "breakdown": {
            "kpi_health": kpi_score,
            "error_penalty": error_score,
            "coverage": coverage_score,
            "momentum": int(momentum_score),
        },
        "win_rate": win_rate,
        "errors_count": len(errors),
        "steps_done": len(done_steps),
        "steps_total": len(expected_steps),
        "recommendations": recommendations,
        "evaluated_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
    }

    _store_cycle_score(total, evaluation)
    return evaluation


def _store_cycle_score(score: int, evaluation: dict) -> None:
    global _mem_cycle_scores
    record = {
        "score": score,
        "ts": int(time.time() * 1000),
        "grade": evaluation["grade"],
        "recommendations": evaluation["recommendations"][:2],
    }
    r = _get_redis()
    if r is not None:
        try:
            pipe = r.pipeline()
            pipe.lpush(CYCLE_SCORES_KEY, json.dumps(record))
            pipe.ltrim(CYCLE_SCORES_KEY, 0, MAX_CYCLE_SCORES - 1)
            pipe.execute()
            return
        except Exception:
            pass
    _mem_cycle_scores.insert(0, record)
    if len(_mem_cycle_scores) > MAX_CYCLE_SCORES:
        _mem_cycle_scores.pop()


def get_cycle_scores(n: int = 10) -> list[dict]:
    """Return the last n cycle evaluation scores (newest first)."""
    r = _get_redis()
    if r is not None:
        try:
            raw = r.lrange(CYCLE_SCORES_KEY, 0, n - 1)
            return [json.loads(item) for item in raw]
        except Exception:
            pass
    return _mem_cycle_scores[:n]
