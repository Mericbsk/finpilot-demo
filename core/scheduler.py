"""FinPilot Scheduler — APScheduler tabanlı sürekli agent döngüsü.

Çalışma döngüsü (her tur):
    1. MarketIntelligenceAgent  — rejim tespiti (sonuç diğer ajanlara geçirilir)
    2. ResearchAgent            — rejim bağlamıyla haber araştırması
    3. BacktestAgent            — strateji testi (rejim-aware)
    4. StrategyOptimizerAgent   — parametre optimizasyonu (haftalık)
    5. PerformanceMonitorAgent  — WARN/STOP kontrolü + KPI güncelleme
    6. ReportAgent              — tüm sonuçları Markdown raporuna özetle
    7. Self-evaluation          — cycle skor hesapla, öneri üret
    8. Tüm sonuçlar core.agent_events ve core.kpi_tracker'a loglanır

Kullanım:
    from core.scheduler import get_scheduler, start_scheduler, stop_scheduler

    scheduler = get_scheduler()
    start_scheduler(symbols=["THYAO.IS", "KCHOL.IS"], interval_minutes=60)

    # Ya da tek seferlik çalıştırmak için:
    from core.scheduler import run_cycle_once
    run_cycle_once(symbols=["THYAO.IS"])
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_scheduler_lock = threading.Lock()
_scheduler_instance: Any = None  # APScheduler instance
_cycle_count = 0
_last_run: str | None = None
_last_status: str = "idle"


# ---------------------------------------------------------------------------
# Core cycle logic
# ---------------------------------------------------------------------------


def run_cycle_once(
    symbols: list[str],
    kelly_fraction: float = 0.5,
    run_optimizer: bool = False,
) -> dict[str, Any]:
    """Tek bir agent döngüsünü senkron çalıştır. Tüm sonuçları döndür.

    Agents communicate via shared context (feedback mechanism):
      - market_intel results → passed as metadata to research + backtest
      - backtest results → used for KPI signal recording
      - monitor results → triggers KPI outcome updates
      - All results → aggregated in ReportAgent
      - Final step: self_evaluate() to score cycle health
    """
    global _cycle_count, _last_run, _last_status

    _last_status = "running"
    t_start = datetime.now(tz=UTC)
    results: dict[str, Any] = {}
    errors: list[str] = []

    try:
        import time

        from agents.backtest_agent import BacktestAgent
        from agents.base import AgentContext
        from agents.market_intelligence import MarketIntelligenceAgent
        from agents.performance_monitor import PerformanceMonitorAgent
        from agents.research_agent import ResearchAgent

        from core.agent_events import log_event
        from core.kpi_tracker import record_signal, self_evaluate

        # --- 1. Market Intelligence (regime detection) ---
        _t = time.perf_counter()
        mi_data: dict[str, Any] = {}
        try:
            mi_ctx = AgentContext(symbols=symbols)
            mi_result = MarketIntelligenceAgent().run(mi_ctx, lookback_days=30, use_llm=False)
            _dur = (time.perf_counter() - _t) * 1000
            mi_data = mi_result.data or {}
            results["market_intel"] = mi_data
            log_event(
                "Market Intelligence",
                "regime_detection",
                "ok" if mi_result.success else "error",
                _dur,
                mi_data.get("market_summary", "") if mi_data else str(mi_result.error),
                symbols,
                "strategy",
            )
        except Exception as exc:
            errors.append(f"market_intel: {exc}")
            logger.warning("Scheduler: market_intel failed: %s", exc)

        # --- 1b. Data Quality Gate — validate symbols before pipeline ---
        _t = time.perf_counter()
        try:
            from agents.data_quality import DataQualityAgent

            dq_ctx = AgentContext(symbols=symbols)
            dq_result = DataQualityAgent().run(dq_ctx)
            _dur = (time.perf_counter() - _t) * 1000
            dq_data = dq_result.data or {}
            results["data_quality"] = dq_data
            if not dq_data.get("passed", True):
                logger.warning(
                    "Scheduler: data quality gate issues: %s",
                    dq_data.get("issues", []),
                )
            log_event(
                "Data Quality",
                "schema_check",
                "ok" if dq_result.success else "error",
                _dur,
                f"quality_score={dq_data.get('quality_score', '?')} passed={dq_data.get('passed', '?')}",
                symbols,
                "quality",
            )
        except Exception as exc:
            errors.append(f"data_quality: {exc}")
            logger.warning("Scheduler: data_quality failed: %s", exc)

        # --- 2. Research — enriched with regime context (feedback from step 1) ---
        _t = time.perf_counter()
        try:
            rs_ctx = AgentContext(
                symbols=symbols,
                metadata={
                    "market_regime": mi_data.get("regime"),
                    "market_summary": mi_data.get("market_summary", ""),
                },
            )
            rs_result = ResearchAgent().run(rs_ctx)
            _dur = (time.perf_counter() - _t) * 1000
            results["research"] = rs_result.data
            log_event(
                "Quant Research",
                "news_fetch",
                "ok" if rs_result.success else "error",
                _dur,
                f"{len(rs_result.data or {})} sembol haber",
                symbols,
                "strategy",
            )
        except Exception as exc:
            errors.append(f"research: {exc}")
            logger.warning("Scheduler: research failed: %s", exc)

        # --- 3. Backtest — uses regime context for strategy selection (feedback) ---
        _t = time.perf_counter()
        bt_data: dict[str, Any] = {}
        try:
            regime_str = mi_data.get("regime", "")
            strategy = "trend" if "bull" in str(regime_str).lower() else "momentum"
            bt_ctx = AgentContext(
                symbols=symbols,
                metadata={"regime": regime_str, "strategy_hint": strategy},
            )
            bt_result = BacktestAgent().run(bt_ctx, strategy=strategy, initial_capital=10_000)
            _dur = (time.perf_counter() - _t) * 1000
            bt_data = bt_result.data or {}
            results["backtest"] = bt_data
            log_event(
                "Combination Testing",
                "backtest",
                "ok" if bt_result.success else "error",
                _dur,
                f"{len(bt_data)} sembol backtest ({strategy})",
                symbols,
                "strategy",
            )
            # Record signals from backtest into KPI tracker
            for sym, bt_sym in bt_data.items():
                if isinstance(bt_sym, dict):
                    direction = "BUY" if bt_sym.get("total_return", 0) > 0 else "SELL"
                    record_signal(
                        symbol=sym,
                        direction=direction,
                        price=bt_sym.get("final_value", 0),
                        score=bt_sym.get("win_rate", 0),
                        rr=bt_sym.get("max_return", 0) / abs(bt_sym.get("max_drawdown", 1) or 1),
                        cycle=_cycle_count + 1,
                    )
        except Exception as exc:
            errors.append(f"backtest: {exc}")
            logger.warning("Scheduler: backtest failed: %s", exc)

        # --- 4. Strategy Optimizer (optional — every N cycles) ---
        if run_optimizer:
            _t = time.perf_counter()
            try:
                from agents.strategy_optimizer import StrategyOptimizerAgent

                opt_ctx = AgentContext(
                    symbols=symbols, metadata={"regime": mi_data.get("regime", "")}
                )
                opt_result = StrategyOptimizerAgent().run(
                    opt_ctx, strategy="momentum", method="grid"
                )
                _dur = (time.perf_counter() - _t) * 1000
                results["optimizer"] = opt_result.data
                log_event(
                    "Strategy Optimizer",
                    "grid_optimize",
                    "ok" if opt_result.success else "error",
                    _dur,
                    f"{len(opt_result.data or {})} sembol optimize edildi",
                    symbols,
                    "strategy",
                )
            except Exception as exc:
                errors.append(f"optimizer: {exc}")
                logger.warning("Scheduler: optimizer failed: %s", exc)

        # --- 5. Performance Monitor — KPI feedback via drawdown outcomes ---
        _t = time.perf_counter()
        pm_data: dict[str, Any] = {}
        try:
            pm_ctx = AgentContext(
                symbols=symbols,
                metadata={"backtest_results": bt_data, "cycle": _cycle_count + 1},
            )
            pm_result = PerformanceMonitorAgent().run(
                pm_ctx, warn_drawdown_pct=10, stop_drawdown_pct=20
            )
            _dur = (time.perf_counter() - _t) * 1000
            pm_data = pm_result.data or {}
            results["monitor"] = pm_data
            portfolio_status = pm_data.get("portfolio_status", "?")
            log_event(
                "Performance Monitor",
                "drawdown_check",
                "ok" if pm_result.success else "error",
                _dur,
                f"Portfolio: {portfolio_status}",
                symbols,
                "quality",
            )
            # Emit feedback to backtest when KPIs are poor (cross-agent feedback loop)
            try:
                from agents.feedback import emit_feedback

                from core.kpi_tracker import get_kpis

                kpis = get_kpis()
                win_rate = kpis.get("win_rate", 0.0)
                if win_rate < 50 and kpis.get("resolved_signals", 0) > 0:
                    emit_feedback(
                        from_agent="performance_monitor",
                        to_agent="backtest",
                        feedback_type="low_win_rate",
                        data={
                            "win_rate": win_rate,
                            "recommendation": "switch to trend strategy",
                            "cycle": _cycle_count + 1,
                        },
                    )
                if pm_data.get("portfolio_status") in ("STOP", "WARN"):
                    emit_feedback(
                        from_agent="performance_monitor",
                        to_agent="ceo",
                        feedback_type="drawdown_alert",
                        data={
                            "portfolio_status": pm_data.get("portfolio_status"),
                            "cycle": _cycle_count + 1,
                        },
                    )
            except Exception:
                pass  # feedback is best-effort
        except Exception as exc:
            errors.append(f"monitor: {exc}")
            logger.warning("Scheduler: monitor failed: %s", exc)

        # --- 6. Report Agent — aggregate all results into a Markdown report ---
        _t = time.perf_counter()
        try:
            from agents.report_agent import ReportAgent

            scan_for_report: dict[str, Any] = {}
            for sym in symbols:
                pm_sym = pm_data.get("symbols", {}).get(sym, {})
                bt_sym = bt_data.get(sym, {}) if isinstance(bt_data, dict) else {}
                scan_for_report[sym] = {
                    "symbol": sym,
                    "direction": True,
                    "regime": mi_data.get("regime", True),
                    "entry_ok": pm_sym.get("status") == "OK",
                    "price": pm_sym.get("last_price", 0),
                    "finpilot_score": bt_sym.get("win_rate", 0),
                    "risk_reward": bt_sym.get("profit_factor", 0),
                    "stop_loss": pm_sym.get("period_high", 0) * 0.95,
                    "take_profit": pm_sym.get("last_price", 0) * 1.1,
                }
            rp_ctx = AgentContext(
                symbols=symbols,
                scan_results=scan_for_report,
                metadata={
                    "analysis_results": {},
                    "risk_results": {},
                    "market_summary": mi_data.get("market_summary", ""),
                    "cycle": _cycle_count + 1,
                },
            )
            rp_result = ReportAgent().run(rp_ctx)
            _dur = (time.perf_counter() - _t) * 1000
            rp_data = rp_result.data or {}
            results["report"] = rp_data.get("report", "")
            log_event(
                "Documentation",
                "cycle_report",
                "ok" if rp_result.success else "error",
                _dur,
                f"Cycle #{_cycle_count + 1} raporu — {len(symbols)} sembol",
                symbols,
                "ops",
            )
        except Exception as exc:
            errors.append(f"report: {exc}")
            logger.warning("Scheduler: report failed: %s", exc)

    except Exception as exc:
        errors.append(f"cycle_fatal: {exc}")
        logger.exception("Scheduler cycle fatal error: %s", exc)
        _last_status = "error"
        return {"errors": errors, "cycle": _cycle_count}

    _cycle_count += 1
    _last_run = t_start.strftime("%Y-%m-%d %H:%M UTC")

    # --- 7. Self-evaluation --- (runs after cycle data is populated)
    try:
        from core.kpi_tracker import self_evaluate

        evaluation = self_evaluate(results)
        results["self_evaluation"] = evaluation
        _last_status = evaluation["grade"]
        log_event(
            "CEO",
            "self_evaluate",
            "ok",
            0.0,
            f"Cycle #{_cycle_count} — Skor: {evaluation['score']}/100 ({evaluation['grade']})",
            symbols,
            "management",
        )
    except Exception as exc:
        errors.append(f"self_eval: {exc}")
        logger.warning("Scheduler: self_eval failed: %s", exc)
        _last_status = "ok"

    try:
        from core.tracing import record_cycle_trace

        record_cycle_trace(
            _cycle_count,
            "cycle_complete",
            _last_status,
            (datetime.now(tz=UTC) - t_start).total_seconds() * 1000,
            f"errors={len(errors)} steps={len(results)}",
        )
    except Exception:
        pass  # tracing is best-effort

    results["errors"] = errors
    results["cycle_number"] = _cycle_count
    results["ran_at"] = _last_run

    logger.info(
        "Scheduler cycle #%d complete — %d agents, %d errors, grade=%s",
        _cycle_count,
        len(
            [k for k in results if k not in ("errors", "cycle_number", "ran_at", "self_evaluation")]
        ),
        len(errors),
        results.get("self_evaluation", {}).get("grade", "?"),
    )
    return results


# ---------------------------------------------------------------------------
# APScheduler integration
# ---------------------------------------------------------------------------


def get_scheduler() -> Any:
    """Mevcut APScheduler instance'ını döndür (yoksa None)."""
    return _scheduler_instance


def start_scheduler(
    symbols: list[str],
    interval_minutes: int = 60,
    kelly_fraction: float = 0.5,
    run_optimizer_every_n: int = 24,  # Her N turda bir optimizer çalıştır
) -> bool:
    """APScheduler başlat. Zaten çalışıyorsa False döner."""
    global _scheduler_instance

    with _scheduler_lock:
        if _scheduler_instance is not None:
            logger.warning("Scheduler zaten çalışıyor.")
            return False

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
        except ImportError:
            logger.error("APScheduler bulunamadı. pip install apscheduler")
            return False

        _scheduler_instance = BackgroundScheduler(
            timezone="UTC",
            job_defaults={"coalesce": True, "max_instances": 1},
        )

        def _scheduled_job() -> None:
            run_optimizer = _cycle_count % run_optimizer_every_n == 0
            run_cycle_once(
                symbols=symbols, kelly_fraction=kelly_fraction, run_optimizer=run_optimizer
            )

        _scheduler_instance.add_job(
            _scheduled_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="finpilot_main_cycle",
            name="FinPilot Main Agent Cycle",
        )
        _scheduler_instance.start()
        logger.info(
            "Scheduler başlatıldı — %d dakikada bir, semboller: %s",
            interval_minutes,
            symbols,
        )
        return True


def stop_scheduler() -> bool:
    """APScheduler'ı durdur. Çalışmıyorsa False döner."""
    global _scheduler_instance

    with _scheduler_lock:
        if _scheduler_instance is None:
            return False
        try:
            _scheduler_instance.shutdown(wait=False)
        except Exception as exc:
            logger.warning("Scheduler durdurma hatası: %s", exc)
        _scheduler_instance = None
        logger.info("Scheduler durduruldu.")
        return True


def scheduler_status() -> dict[str, Any]:
    """Mevcut scheduler durumunu döndür."""
    return {
        "running": _scheduler_instance is not None,
        "cycle_count": _cycle_count,
        "last_run": _last_run,
        "last_status": _last_status,
    }
