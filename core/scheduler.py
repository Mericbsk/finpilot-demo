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
    start_scheduler(symbols=["AAPL", "MSFT", "NVDA"], interval_minutes=60)

    # Ya da tek seferlik çalıştırmak için:
    from core.scheduler import run_cycle_once
    run_cycle_once(symbols=["AAPL"])
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
_eval_last_run: str | None = None


def _run_eval_job(symbols: list[str]) -> None:
    """Run offline eval harness and save report to shared agent state."""
    import asyncio

    try:
        from tests.eval.eval_harness import run_eval

        report = asyncio.run(run_eval(symbols))

        try:
            from core.agent_state import save_agent_result

            save_agent_result("eval", symbols, report)
        except Exception as save_exc:
            logger.warning("Eval: state save failed: %s", save_exc)

        global _eval_last_run

        _eval_last_run = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
        grade = "ok" if report.get("overall_pass") else "warn"
        logger.info(
            "Eval job completed — overall_pass=%s grade=%s", report.get("overall_pass"), grade
        )

        # Sprint 5 (S5-3): Quality gate — degrade on eval failure
        try:
            from core.quality_gate import clear_degraded, set_degraded

            if not report.get("overall_pass"):
                metrics = report.get("metrics", {}) or {}
                failing = [k for k, v in metrics.items() if isinstance(v, dict) and not v.get("pass")]
                set_degraded(
                    reason=f"eval failed: {','.join(failing) or 'unknown'}",
                    eval_report=report,
                )
            else:
                clear_degraded()
        except Exception as gate_exc:
            logger.warning("Quality gate update failed: %s", gate_exc)
    except Exception as exc:
        logger.warning("Eval job failed: %s", exc)


def _run_reconcile_job() -> None:
    """Sprint 5 (S5-1): Walk open signals, fetch T+N closes, record outcomes."""
    try:
        from core.outcome_reconciler import reconcile_open_signals

        summary = reconcile_open_signals()
        logger.info(
            "Reconcile job: reconciled=%d skipped_age=%d skipped_data=%d errors=%d",
            summary["reconciled"],
            summary["skipped_age"],
            summary["skipped_data"],
            len(summary["errors"]),
        )
    except Exception as exc:
        logger.warning("Reconcile job failed: %s", exc)


def _run_calibration_job() -> None:
    """Sprint 5 (S5-4): Refit score→P(win) mapping from resolved signals."""
    try:
        from core.calibration import refit_calibration

        model = refit_calibration()
        logger.info(
            "Calibration refit: n=%d global_p=%.3f",
            model.get("n_samples", 0),
            model.get("global_win_rate", 0.0),
        )
    except Exception as exc:
        logger.warning("Calibration job failed: %s", exc)


def _run_weekly_report_job() -> None:
    """Sprint 5 (S5-7): Generate public weekly Markdown KPI report."""
    try:
        from scripts.weekly_report import generate_weekly_report

        _, path = generate_weekly_report()
        if path:
            logger.info("Weekly report generated: %s", path)
    except Exception as exc:
        logger.warning("Weekly report job failed: %s", exc)


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
        from agents.scanner_agent import ScannerAgent

        from core.agent_events import log_event
        from core.agent_state import save_agent_result
        from core.kpi_tracker import record_signal, self_evaluate

        # --- 0. Scanner — generate fresh technical signals for downstream agents ---
        _t = time.perf_counter()
        scan_data: dict[str, Any] = {}
        try:
            sc_ctx = AgentContext(symbols=symbols)
            sc_result = ScannerAgent().run(sc_ctx, kelly_fraction=kelly_fraction)
            _dur = (time.perf_counter() - _t) * 1000
            scan_data = sc_result.data or {}
            results["scan"] = scan_data
            try:
                save_agent_result("scan", symbols, scan_data)
            except Exception as save_exc:
                logger.warning("Scheduler: scan state save failed: %s", save_exc)
            log_event(
                "Scanner",
                "evaluate_symbols",
                "ok" if sc_result.success else "error",
                _dur,
                f"{len(scan_data)} sembol tarandı",
                symbols,
                "strategy",
            )
        except Exception as exc:
            errors.append(f"scanner: {exc}")
            logger.warning("Scheduler: scanner failed: %s", exc)

        # --- 1. Market Intelligence (regime detection) ---
        _t = time.perf_counter()
        mi_data: dict[str, Any] = {}
        try:
            mi_ctx = AgentContext(symbols=symbols)
            mi_result = MarketIntelligenceAgent().run(mi_ctx, lookback_days=30, use_llm=True)
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

        # --- 2. Research — enriched with regime context + CEO scan results ---
        _t = time.perf_counter()
        try:
            # Load latest CEO scan results from shared state (best-effort)
            _ceo_scan: dict[str, Any] = {}
            try:
                from core.agent_state import get_latest_scan

                _ceo_scan = get_latest_scan(symbols) or {}
            except Exception:
                pass

            rs_ctx = AgentContext(
                symbols=symbols,
                scan_results=_ceo_scan or None,
                metadata={
                    "market_regime": mi_data.get("regime"),
                    "market_summary": mi_data.get("market_summary", ""),
                    "ceo_scan_available": bool(_ceo_scan),
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
                scan_results=scan_data or None,
                metadata={
                    "regime": regime_str,
                    "strategy_hint": strategy,
                    "scan_available": bool(scan_data),
                },
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
            # Sprint 5 (S5-5): also open a paper-portfolio position so we get real P&L
            for sym, bt_sym in bt_data.items():
                if isinstance(bt_sym, dict):
                    direction = "BUY" if bt_sym.get("total_return", 0) > 0 else "SELL"
                    entry_price = float(bt_sym.get("final_value", 0) or 0)
                    score_val = float(bt_sym.get("win_rate", 0) or 0)
                    record_signal(
                        symbol=sym,
                        direction=direction,
                        price=entry_price,
                        score=score_val,
                        rr=bt_sym.get("max_return", 0) / abs(bt_sym.get("max_drawdown", 1) or 1),
                        cycle=_cycle_count + 1,
                    )
                    if entry_price > 0:
                        try:
                            import time as _t_paper

                            from core.paper_portfolio import open_position

                            sig_id = f"{sym}_{_cycle_count + 1}_{int(_t_paper.time())}"
                            open_position(
                                signal_id=sig_id,
                                symbol=sym,
                                direction=direction,
                                entry_price=entry_price,
                                score=score_val,
                                cycle=_cycle_count + 1,
                            )
                        except Exception as paper_exc:
                            logger.debug("paper open failed for %s: %s", sym, paper_exc)
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
                    # S3-5: Telegram critical alert on drawdown
                    try:
                        from telegram_alerts import TelegramNotifier

                        status_str = pm_data.get("portfolio_status")
                        emoji = "🛑" if status_str == "STOP" else "⚠️"
                        worst_sym = ""
                        try:
                            sym_map = pm_data.get("symbols", {})
                            if isinstance(sym_map, dict) and sym_map:
                                worst = min(
                                    sym_map.items(),
                                    key=lambda kv: kv[1].get("drawdown_pct", 0)
                                    if isinstance(kv[1], dict)
                                    else 0,
                                )
                                worst_sym = (
                                    f"\nEn kötü: {worst[0]} "
                                    f"DD={worst[1].get('drawdown_pct', '?')}%"
                                )
                        except Exception:  # noqa: BLE001, S110
                            pass
                        msg = (
                            f"{emoji} *PORTFÖY {status_str}* — Cycle #{_cycle_count + 1}"
                            f"{worst_sym}"
                            f"\nWin rate: {win_rate:.1f}% | Resolved: {kpis.get('resolved_signals', 0)}"
                        )
                        TelegramNotifier()._send_message(msg)
                    except Exception as tex:  # noqa: BLE001
                        logger.warning("Scheduler: telegram drawdown alert failed: %s", tex)
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

            # S3-3: Telegram alert for symbols with entry_ok=True
            try:
                from telegram_alerts import TelegramNotifier

                from core.agent_state import mark_alert_sent, was_alert_sent

                # Sprint 5 (S5-3): suppress alerts when system is degraded
                try:
                    from core.quality_gate import is_degraded as _is_degraded

                    _gate_degraded = _is_degraded()
                except Exception:  # noqa: BLE001
                    _gate_degraded = False

                entries = (
                    []
                    if _gate_degraded
                    else [
                        (sym, sig)
                        for sym, sig in scan_for_report.items()
                        if sig.get("entry_ok") and not was_alert_sent(sym, _cycle_count + 1)
                    ]
                )
                if entries:
                    notifier = TelegramNotifier()
                    for sym, sig in entries[:10]:  # cap to 10 per cycle
                        try:
                            price = float(sig.get("price", 0) or 0)
                            sl = float(sig.get("stop_loss", 0) or 0)
                            tp = float(sig.get("take_profit", 0) or 0)
                            sl_pct = abs((price - sl) / price * 100) if price else 0.0
                            signal_data = {
                                "symbol": sym,
                                "price": round(price, 4),
                                "stop_loss": round(sl, 4),
                                "stop_loss_percent": sl_pct,
                                "take_profit": round(tp, 4),
                                "risk_reward": float(sig.get("risk_reward", 0) or 0),
                                "position_size": 0,
                                "score": int(round(float(sig.get("finpilot_score", 0) or 0))),
                                "filter_score": 3,
                                "is_premium_symbol": False,
                                "timestamp": t_start.strftime("%Y-%m-%d %H:%M UTC"),
                            }
                            notifier.send_signal_alert(signal_data)
                            mark_alert_sent(sym, _cycle_count + 1)
                        except Exception as ie:  # noqa: BLE001
                            logger.warning(
                                "Scheduler: telegram entry_ok send failed for %s: %s", sym, ie
                            )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Scheduler: telegram entry_ok hook failed: %s", exc)
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

    # --- 8. Advisory post-step (Sprint 3 — S3-2/S3-6) ---
    # Every N cycles, feed scan + KPI summary to competitive_intel + cto advisors
    # for an autonomous strategic review. Results are persisted to advisory_memory
    # under user_id="scheduler" so the UI / future runs can read them.
    try:
        _advisory_every_n = 10  # ~10 cycles ≈ weekly at hourly interval
        if _cycle_count > 0 and _cycle_count % _advisory_every_n == 0:
            from agents.advisory import advisory_agent_for

            from core.advisory_memory import append_message

            top_signals: list[str] = []
            try:
                for sym, sig in (scan_data or {}).items():  # noqa: F821 (defined above)
                    if isinstance(sig, dict) and sig.get("entry_ok"):
                        top_signals.append(
                            f"{sym}: skor={sig.get('finpilot_score', '?')} "
                            f"R/R={sig.get('risk_reward', '?')}"
                        )
            except Exception:  # noqa: BLE001, S110
                pass
            top_block = "\n".join(top_signals[:10]) if top_signals else "Aktif sinyal yok."
            kpi_block = ""
            try:
                from core.kpi_tracker import get_kpis

                _k = get_kpis()
                kpi_block = (
                    f"Win rate: {_k.get('win_rate', 0):.1f}% | "
                    f"Resolved: {_k.get('resolved_signals', 0)} | "
                    f"Open: {_k.get('open_signals', 0)}"
                )
            except Exception:  # noqa: BLE001, S110
                pass

            review_question = (
                f"Cycle #{_cycle_count} otomatik strateji incelemesi. "
                "Mevcut sinyaller ve KPI'lar göz önüne alındığında en kritik "
                "gelişme nedir ve önerin nedir? (Kısa, 3 madde)"
            )
            review_context = (
                f"Top sinyaller:\n{top_block}\n\n"
                f"KPI özeti: {kpi_block or '?'}\n"
                f"Market regime: {mi_data.get('regime', '?')}"
            )
            review_results: dict[str, Any] = {}
            for advisor_key in ("competitive_intel", "cto"):
                try:
                    agent = advisory_agent_for(advisor_key)
                    a_ctx = AgentContext(symbols=symbols)
                    a_res = agent.run(
                        a_ctx,
                        question=review_question,
                        context_str=review_context,
                    )
                    if a_res.success:
                        advice = (a_res.data or {}).get("advice", "")
                        review_results[advisor_key] = advice
                        append_message(advisor_key, "scheduler", "user", review_question)
                        append_message(
                            advisor_key,
                            "scheduler",
                            "assistant",
                            advice,
                            extra={"cycle": _cycle_count, "auto": True},
                        )
                except Exception as ae:  # noqa: BLE001
                    logger.warning(
                        "Scheduler: advisory review failed for %s: %s", advisor_key, ae
                    )
            if review_results:
                results["advisory_review"] = review_results
                try:
                    save_agent_result("advisory_review", symbols, review_results)
                except Exception:  # noqa: BLE001, S110
                    pass
                log_event(
                    "Advisory",
                    "auto_review",
                    "ok",
                    0.0,
                    f"Cycle #{_cycle_count} — {len(review_results)} danışman incelemesi",
                    symbols,
                    "management",
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scheduler: advisory post-step failed: %s", exc)
        errors.append(f"advisory_post: {exc}")

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

        # Autonomous eval job — always runs hourly regardless of main cycle interval
        def _eval_job_wrapper() -> None:
            _run_eval_job(symbols)

        _scheduler_instance.add_job(
            _eval_job_wrapper,
            trigger=IntervalTrigger(hours=1),
            id="finpilot_eval_job",
            name="FinPilot Autonomous Eval",
        )

        # Sprint 5 — closed-loop jobs
        _scheduler_instance.add_job(
            _run_reconcile_job,
            trigger=IntervalTrigger(hours=6),
            id="finpilot_reconcile_job",
            name="FinPilot Outcome Reconciler",
        )
        _scheduler_instance.add_job(
            _run_calibration_job,
            trigger=IntervalTrigger(hours=24),
            id="finpilot_calibration_job",
            name="FinPilot Score Calibration",
        )
        _scheduler_instance.add_job(
            _run_weekly_report_job,
            trigger=IntervalTrigger(days=7),
            id="finpilot_weekly_report_job",
            name="FinPilot Weekly Report",
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
        "eval_last_run": _eval_last_run,
    }
