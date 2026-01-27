"""
Performance Report Generator for FinPilot.

Generates comprehensive HTML and PDF reports from backtest results.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .backtest_engine import MonteCarloResult, PerformanceMetrics, WalkForwardResult

logger = logging.getLogger(__name__)


# ============================================================================
# REPORT DATA STRUCTURES
# ============================================================================


@dataclass
class ReportConfig:
    """Report generation configuration."""

    title: str = "FinPilot Backtest Report"
    author: str = "FinPilot AI"
    strategy_name: str = "Unknown Strategy"

    # Output
    output_dir: str = "reports"
    include_charts: bool = True
    include_trades: bool = True

    # Styling
    theme: str = "dark"  # "dark" or "light"


@dataclass
class FullReport:
    """Complete backtest report data."""

    # Metadata
    generated_at: str
    strategy_name: str
    period_start: str
    period_end: str

    # Core Metrics
    main_metrics: Dict[str, Any]

    # Walk-Forward
    walk_forward_summary: Optional[Dict[str, Any]] = None
    walk_forward_folds: Optional[List[Dict[str, Any]]] = None

    # Monte Carlo
    monte_carlo: Optional[Dict[str, Any]] = None

    # Trade Log
    trades: Optional[List[Dict[str, Any]]] = None

    # Equity Curve Data
    equity_curve: Optional[List[float]] = None
    drawdown_curve: Optional[List[float]] = None
    dates: Optional[List[str]] = None


# ============================================================================
# HTML REPORT GENERATOR
# ============================================================================


class HTMLReportGenerator:
    """Generates interactive HTML reports."""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()

    def generate(self, report: FullReport) -> str:
        """
        Generate HTML report string.

        Args:
            report: FullReport with all data

        Returns:
            HTML string
        """
        theme_colors = self._get_theme_colors()

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <style>
        :root {{
            --bg-primary: {theme_colors['bg_primary']};
            --bg-secondary: {theme_colors['bg_secondary']};
            --bg-card: {theme_colors['bg_card']};
            --text-primary: {theme_colors['text_primary']};
            --text-secondary: {theme_colors['text_secondary']};
            --accent: {theme_colors['accent']};
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--bg-secondary);
        }}

        header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }}

        header .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        .meta-info {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}

        .section {{
            margin-bottom: 3rem;
        }}

        .section h2 {{
            font-size: 1.5rem;
            color: var(--accent);
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }}

        .metric-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--bg-secondary);
        }}

        .metric-card .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .metric-card .value {{
            font-size: 2rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }}

        .metric-card .value.positive {{
            color: var(--success);
        }}

        .metric-card .value.negative {{
            color: var(--danger);
        }}

        .metric-card .value.neutral {{
            color: var(--text-primary);
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        @media (max-width: 768px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--bg-secondary);
        }}

        th {{
            background: var(--bg-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge.success {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
        }}

        .badge.danger {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
        }}

        .badge.warning {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning);
        }}

        .progress-bar {{
            height: 8px;
            background: var(--bg-secondary);
            border-radius: 4px;
            overflow: hidden;
        }}

        .progress-bar .fill {{
            height: 100%;
            border-radius: 4px;
        }}

        .summary-box {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            border: 1px solid var(--bg-secondary);
        }}

        .summary-box h3 {{
            margin-bottom: 1rem;
            color: var(--accent);
        }}

        footer {{
            text-align: center;
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--bg-secondary);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 {self.config.title}</h1>
            <p class="subtitle">{report.strategy_name}</p>
            <div class="meta-info">
                <span>📅 {report.period_start} → {report.period_end}</span>
                <span>🕐 Oluşturulma: {report.generated_at}</span>
            </div>
        </header>

        {self._render_metrics_section(report)}

        {self._render_risk_section(report)}

        {self._render_trade_section(report)}

        {self._render_walkforward_section(report)}

        {self._render_montecarlo_section(report)}

        <footer>
            <p>FinPilot Backtest Report v2.0 | {self.config.author}</p>
        </footer>
    </div>
</body>
</html>
"""
        return html

    def _get_theme_colors(self) -> Dict[str, str]:
        """Get color scheme based on theme."""
        if self.config.theme == "light":
            return {
                "bg_primary": "#f8fafc",
                "bg_secondary": "#e2e8f0",
                "bg_card": "#ffffff",
                "text_primary": "#1e293b",
                "text_secondary": "#64748b",
                "accent": "#3b82f6",
            }
        else:
            return {
                "bg_primary": "#0f172a",
                "bg_secondary": "#1e293b",
                "bg_card": "#1e293b",
                "text_primary": "#f8fafc",
                "text_secondary": "#94a3b8",
                "accent": "#60a5fa",
            }

    def _render_metrics_section(self, report: FullReport) -> str:
        """Render main metrics section."""
        m = report.main_metrics

        # Determine value classes
        return_class = "positive" if m.get("total_return", 0) >= 0 else "negative"
        sharpe_class = (
            "positive"
            if m.get("sharpe_ratio", 0) >= 1
            else ("neutral" if m.get("sharpe_ratio", 0) >= 0 else "negative")
        )

        return f"""
        <section class="section">
            <h2>📈 Temel Performans Metrikleri</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="label">Toplam Getiri</div>
                    <div class="value {return_class}">{m.get('total_return', 0):.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Yıllık Getiri</div>
                    <div class="value {return_class}">{m.get('annualized_return', 0):.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Sharpe Oranı</div>
                    <div class="value {sharpe_class}">{m.get('sharpe_ratio', 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Sortino Oranı</div>
                    <div class="value neutral">{m.get('sortino_ratio', 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Calmar Oranı</div>
                    <div class="value neutral">{m.get('calmar_ratio', 0):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Volatilite</div>
                    <div class="value neutral">{m.get('volatility', 0):.2%}</div>
                </div>
            </div>
        </section>
        """

    def _render_risk_section(self, report: FullReport) -> str:
        """Render risk metrics section."""
        m = report.main_metrics

        max_dd = m.get("max_drawdown", 0)
        dd_bar_width = min(max_dd * 100 * 2, 100)  # Scale for visibility

        return f"""
        <section class="section">
            <h2>⚠️ Risk Metrikleri</h2>
            <div class="two-column">
                <div class="summary-box">
                    <h3>Drawdown Analizi</h3>
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Maksimum Drawdown</span>
                            <span style="color: var(--danger); font-weight: bold;">{max_dd:.2%}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="fill" style="width: {dd_bar_width}%; background: var(--danger);"></div>
                        </div>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 0.9rem;">
                        Maksimum çekilme süresi: {m.get('max_drawdown_duration', 0)} gün
                    </p>
                </div>

                <div class="summary-box">
                    <h3>Risk Değerleri (VaR)</h3>
                    <table>
                        <tr>
                            <td>VaR (95%)</td>
                            <td style="text-align: right; color: var(--warning);">{m.get('var_95', 0):.2%}</td>
                        </tr>
                        <tr>
                            <td>CVaR (95%)</td>
                            <td style="text-align: right; color: var(--danger);">{m.get('cvar_95', 0):.2%}</td>
                        </tr>
                    </table>
                    <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 1rem;">
                        %95 güven seviyesinde günlük risk değerleri
                    </p>
                </div>
            </div>
        </section>
        """

    def _render_trade_section(self, report: FullReport) -> str:
        """Render trade statistics section."""
        m = report.main_metrics

        win_rate = m.get("win_rate", 0)
        win_bar_width = win_rate * 100

        pf = m.get("profit_factor", 0)
        pf_class = "success" if pf >= 1.5 else ("warning" if pf >= 1 else "danger")

        return f"""
        <section class="section">
            <h2>💹 İşlem İstatistikleri</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="label">Toplam İşlem</div>
                    <div class="value neutral">{m.get('total_trades', 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Kazanma Oranı</div>
                    <div class="value neutral">{win_rate:.1%}</div>
                    <div class="progress-bar" style="margin-top: 0.5rem;">
                        <div class="fill" style="width: {win_bar_width}%; background: var(--success);"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="label">Profit Factor</div>
                    <div class="value">
                        <span class="badge {pf_class}">{pf:.2f}</span>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="label">Ortalama Kazanç</div>
                    <div class="value positive">{m.get('avg_win', 0):.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Ortalama Kayıp</div>
                    <div class="value negative">{m.get('avg_loss', 0):.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Ortalama Tutma</div>
                    <div class="value neutral">{m.get('avg_holding_days', 0):.1f} gün</div>
                </div>
            </div>
        </section>
        """

    def _render_walkforward_section(self, report: FullReport) -> str:
        """Render walk-forward analysis section."""
        if not report.walk_forward_summary:
            return ""

        wf = report.walk_forward_summary
        robust = wf.get("robust", False)
        robust_badge = (
            '<span class="badge success">ROBUST</span>'
            if robust
            else '<span class="badge danger">OVERFIT RİSKİ</span>'
        )

        return f"""
        <section class="section">
            <h2>🔄 Walk-Forward Analizi</h2>
            <div class="summary-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h3>Robustness Testi</h3>
                    {robust_badge}
                </div>
                <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
                    <div>
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Fold Sayısı</div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{wf.get('n_folds', 0)}</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Train Sharpe (Ort.)</div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{wf.get('avg_train_sharpe', 0):.2f}</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Test Sharpe (Ort.)</div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{wf.get('avg_test_sharpe', 0):.2f}</div>
                    </div>
                    <div>
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">Degradasyon</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: {'var(--danger)' if wf.get('sharpe_degradation', 0) > 0.3 else 'var(--success)'};">
                            {wf.get('sharpe_degradation', 0):.1%}
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """

    def _render_montecarlo_section(self, report: FullReport) -> str:
        """Render Monte Carlo analysis section."""
        if not report.monte_carlo:
            return ""

        mc = report.monte_carlo

        return f"""
        <section class="section">
            <h2>🎲 Monte Carlo Simülasyonu</h2>
            <div class="two-column">
                <div class="summary-box">
                    <h3>Equity Dağılımı ({mc.get('n_simulations', 0)} simülasyon)</h3>
                    <table>
                        <tr>
                            <td>Ortalama</td>
                            <td style="text-align: right; font-weight: bold;">${mc.get('mean_equity', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td>Medyan</td>
                            <td style="text-align: right;">${mc.get('median_equity', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td>5. Yüzdelik (En Kötü)</td>
                            <td style="text-align: right; color: var(--danger);">${mc.get('equity_5th', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td>95. Yüzdelik (En İyi)</td>
                            <td style="text-align: right; color: var(--success);">${mc.get('equity_95th', 0):,.2f}</td>
                        </tr>
                    </table>
                </div>

                <div class="summary-box">
                    <h3>Risk Olasılıkları</h3>
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Zarar Olasılığı</span>
                            <span style="color: var(--warning);">{mc.get('prob_loss', 0):.1%}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="fill" style="width: {mc.get('prob_loss', 0) * 100}%; background: var(--warning);"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Yıkım Olasılığı (&gt;50% kayıp)</span>
                            <span style="color: var(--danger);">{mc.get('prob_ruin', 0):.1%}</span>
                        </div>
                        <div class="progress-bar">
                            <div class="fill" style="width: {mc.get('prob_ruin', 0) * 100}%; background: var(--danger);"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>Beklenen Max Drawdown</span>
                            <span>{mc.get('expected_max_drawdown', 0):.2%}</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """

    def save(self, report: FullReport, filename: Optional[str] = None) -> str:
        """
        Generate and save HTML report.

        Args:
            report: FullReport with all data
            filename: Output filename (optional)

        Returns:
            Path to saved file
        """
        # Create output directory
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_report_{timestamp}.html"

        filepath = output_dir / filename

        # Generate and save
        html = self.generate(report)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Report saved: {filepath}")
        return str(filepath)


# ============================================================================
# JSON REPORT GENERATOR
# ============================================================================


class JSONReportGenerator:
    """Generates JSON reports for programmatic access."""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()

    def generate(self, report: FullReport) -> Dict[str, Any]:
        """Generate JSON-serializable report."""
        return {
            "metadata": {
                "generated_at": report.generated_at,
                "strategy_name": report.strategy_name,
                "period_start": report.period_start,
                "period_end": report.period_end,
                "generator": "FinPilot v2.0",
            },
            "metrics": report.main_metrics,
            "walk_forward": report.walk_forward_summary,
            "monte_carlo": report.monte_carlo,
            "trades_summary": {"count": len(report.trades) if report.trades else 0},
        }

    def save(self, report: FullReport, filename: Optional[str] = None) -> str:
        """Save JSON report."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_report_{timestamp}.json"

        filepath = output_dir / filename

        data = self.generate(report)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON report saved: {filepath}")
        return str(filepath)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_report(
    metrics: PerformanceMetrics,
    strategy_name: str = "FinPilot Strategy",
    walk_forward: Optional[Dict] = None,
    monte_carlo: Optional[Dict] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> FullReport:
    """
    Create a FullReport from metrics and optional analysis.

    Args:
        metrics: PerformanceMetrics from backtest
        strategy_name: Name of the strategy
        walk_forward: Walk-forward summary dict
        monte_carlo: Monte Carlo result dict
        period_start: Start date string
        period_end: End date string

    Returns:
        FullReport ready for rendering
    """
    return FullReport(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        strategy_name=strategy_name,
        period_start=period_start or "N/A",
        period_end=period_end or "N/A",
        main_metrics=metrics.to_dict(),
        walk_forward_summary=walk_forward,
        monte_carlo=monte_carlo,
        equity_curve=metrics.equity_curve.tolist() if len(metrics.equity_curve) > 0 else None,
        drawdown_curve=metrics.drawdown_curve.tolist() if len(metrics.drawdown_curve) > 0 else None,
    )


def generate_html_report(
    metrics: PerformanceMetrics,
    strategy_name: str = "FinPilot Strategy",
    output_dir: str = "reports",
    **kwargs,
) -> str:
    """
    Quick function to generate and save HTML report.

    Args:
        metrics: PerformanceMetrics from backtest
        strategy_name: Name of the strategy
        output_dir: Output directory
        **kwargs: Additional report data (walk_forward, monte_carlo, etc.)

    Returns:
        Path to saved report
    """
    report = create_report(metrics, strategy_name, **kwargs)

    config = ReportConfig(strategy_name=strategy_name, output_dir=output_dir)
    generator = HTMLReportGenerator(config)

    return generator.save(report)


__all__ = [
    "ReportConfig",
    "FullReport",
    "HTMLReportGenerator",
    "JSONReportGenerator",
    "create_report",
    "generate_html_report",
]
