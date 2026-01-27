import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# Backtest Engine Integration
try:
    from drl.backtest_engine import (
        BacktestConfig,
        MonteCarloSimulator,
        VectorizedBacktest,
        WalkForwardOptimizer,
    )
    from drl.report_generator import HTMLReportGenerator, ReportConfig, create_report

    BACKTEST_AVAILABLE = True
except ImportError:
    BACKTEST_AVAILABLE = False


def render_backtest_section():
    """Render interactive backtest section."""
    st.markdown("## 🧪 Gelişmiş Backtest Motoru")

    if not BACKTEST_AVAILABLE:
        st.warning(
            "Backtest modülü yüklenemedi. Lütfen drl/backtest_engine.py dosyasını kontrol edin."
        )
        return

    # Settings
    col1, col2, col3 = st.columns(3)

    with col1:
        initial_capital = st.number_input(
            "Başlangıç Sermayesi ($)", min_value=1000, max_value=1000000, value=10000, step=1000
        )

    with col2:
        position_size = st.slider(
            "Pozisyon Büyüklüğü (%)", min_value=5, max_value=50, value=10, step=5
        )

    with col3:
        n_simulations = st.select_slider(
            "Monte Carlo Simülasyon", options=[100, 500, 1000, 5000], value=500
        )

    # Risk settings
    with st.expander("⚙️ Risk Yönetimi Ayarları", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            stop_loss = st.slider("Stop Loss (%)", 1, 20, 5)
        with col2:
            take_profit = st.slider("Take Profit (%)", 5, 50, 15)
        with col3:
            commission = st.number_input("Komisyon (bps)", 0, 50, 10)

    # Symbol selection
    st.markdown("### 📊 Sembol Seçimi")

    symbol_input = st.text_input(
        "Semboller (virgülle ayırın)", value="AAPL, MSFT, NVDA", help="Örn: AAPL, MSFT, GOOGL"
    )

    symbols = [s.strip().upper() for s in symbol_input.split(",") if s.strip()]

    # Period
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("Backtest Dönemi", options=["3mo", "6mo", "1y", "2y"], index=2)
    with col2:
        strategy_type = st.selectbox(
            "Strateji", options=["Momentum", "Mean Reversion", "DRL (Eğer mevcut)"], index=0
        )

    # Run button
    if st.button("🚀 Backtest Çalıştır", type="primary", use_container_width=True):
        with st.spinner("Backtest çalıştırılıyor..."):
            try:
                results = run_backtest_analysis(
                    symbols=symbols,
                    period=period,
                    initial_capital=initial_capital,
                    position_size_pct=position_size / 100,
                    stop_loss_pct=stop_loss / 100,
                    take_profit_pct=take_profit / 100,
                    commission_pct=commission / 10000,
                    n_simulations=n_simulations,
                    strategy_type=strategy_type,
                )

                if results:
                    render_backtest_results(results)
                else:
                    st.error("Backtest başarısız oldu. Lütfen sembolleri kontrol edin.")

            except Exception as e:
                st.error(f"Backtest hatası: {e}")
                logger.exception("Backtest error")


def run_backtest_analysis(
    symbols: list,
    period: str,
    initial_capital: float,
    position_size_pct: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    commission_pct: float,
    n_simulations: int,
    strategy_type: str,
) -> dict:
    """Run complete backtest analysis."""
    import yfinance as yf

    # Download data
    all_data = {}
    for symbol in symbols:
        try:
            df = yf.download(symbol, period=period, progress=False)
            if df is not None and not df.empty:
                # Flatten multi-level columns if needed
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                all_data[symbol] = df
        except ConnectionError as e:
            logger.error(f"Bağlantı hatası ({symbol}): {e}")
        except ValueError as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg:
                logger.warning(f"Rate limit aşıldı ({symbol}): Lütfen bekleyin")
            else:
                logger.warning(f"Değer hatası ({symbol}): {e}")
        except Exception as e:
            logger.warning(f"Veri indirilemedi ({symbol}): {e}")

    if not all_data:
        return None

    # Use first symbol for main analysis
    symbol = list(all_data.keys())[0]
    df = all_data[symbol].copy()

    # Generate signals based on strategy
    if strategy_type == "Momentum":
        signals = generate_momentum_signals(df)
    elif strategy_type == "Mean Reversion":
        signals = generate_mean_reversion_signals(df)
    else:
        signals = generate_momentum_signals(df)  # Default

    # Create backtest config
    config = BacktestConfig(
        initial_capital=initial_capital,
        position_size_pct=position_size_pct,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        commission_pct=commission_pct,
        n_simulations=n_simulations,
    )

    # Run main backtest
    df["close"] = df["Close"]
    df["signal"] = signals

    engine = VectorizedBacktest(config)
    metrics = engine.run_with_sizing(df)

    # Run Monte Carlo
    mc = MonteCarloSimulator(config)
    mc_result = mc.run_bootstrap(metrics.daily_returns)

    # Run Walk-Forward (if enough data)
    wf_summary = None
    if len(df) > 100:
        try:

            def signal_gen(d):
                return (
                    generate_momentum_signals(d)
                    if strategy_type == "Momentum"
                    else generate_mean_reversion_signals(d)
                )

            wfo = WalkForwardOptimizer(config)
            wfo.run_anchored(df, signal_gen)
            wf_summary = wfo.summary()
        except Exception as e:
            logger.warning(f"Walk-forward failed: {e}")

    return {
        "symbol": symbol,
        "metrics": metrics,
        "mc_result": mc_result,
        "wf_summary": wf_summary,
        "config": config,
        "period": period,
        "strategy": strategy_type,
    }


def generate_momentum_signals(df: pd.DataFrame) -> pd.Series:
    """Generate momentum-based trading signals."""
    signals = pd.Series(0, index=df.index)

    if len(df) < 50:
        return signals

    # Calculate indicators
    close = df["Close"] if "Close" in df.columns else df["close"]
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()

    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Signals
    # Buy: Price crosses above MA20, RSI < 70
    buy_condition = (close > ma20) & (close.shift(1) <= ma20.shift(1)) & (rsi < 70)
    # Sell: Price crosses below MA20 or RSI > 80
    sell_condition = (close < ma20) & (close.shift(1) >= ma20.shift(1)) | (rsi > 80)

    signals[buy_condition] = 1
    signals[sell_condition] = -1

    return signals


def generate_mean_reversion_signals(df: pd.DataFrame) -> pd.Series:
    """Generate mean reversion trading signals."""
    signals = pd.Series(0, index=df.index)

    if len(df) < 20:
        return signals

    close = df["Close"] if "Close" in df.columns else df["close"]

    # Bollinger Bands
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    upper_band = ma20 + 2 * std20
    lower_band = ma20 - 2 * std20

    # Signals
    # Buy: Price touches lower band (oversold)
    buy_condition = close < lower_band
    # Sell: Price touches upper band (overbought)
    sell_condition = close > upper_band

    signals[buy_condition] = 1
    signals[sell_condition] = -1

    return signals


def render_backtest_results(results: dict):
    """Render backtest results in dashboard."""
    metrics = results["metrics"]
    mc_result = results["mc_result"]
    wf_summary = results.get("wf_summary")

    st.markdown("---")
    st.markdown(f"### 📈 Backtest Sonuçları: {results['symbol']}")
    st.caption(f"Strateji: {results['strategy']} | Dönem: {results['period']}")

    # Main metrics cards
    col1, col2, col3, col4 = st.columns(4)

    return_color = "green" if metrics.total_return >= 0 else "red"
    sharpe_color = (
        "green" if metrics.sharpe_ratio >= 1 else ("orange" if metrics.sharpe_ratio >= 0 else "red")
    )

    with col1:
        st.metric(
            "Toplam Getiri",
            f"{metrics.total_return:.2%}",
            delta=f"Yıllık: {metrics.annualized_return:.2%}",
        )

    with col2:
        st.metric(
            "Sharpe Oranı",
            f"{metrics.sharpe_ratio:.2f}",
            delta=f"Sortino: {metrics.sortino_ratio:.2f}",
        )

    with col3:
        st.metric(
            "Max Drawdown",
            f"{metrics.max_drawdown:.2%}",
            delta=f"-{metrics.max_drawdown_duration} gün",
            delta_color="inverse",
        )

    with col4:
        st.metric(
            "Toplam İşlem", f"{metrics.total_trades}", delta=f"Win Rate: {metrics.win_rate:.1%}"
        )

    # Detailed metrics
    with st.expander("📊 Detaylı Metrikler", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Risk Metrikleri**")
            st.write(f"- Volatilite: {metrics.volatility:.2%}")
            st.write(f"- VaR (95%): {metrics.var_95:.2%}")
            st.write(f"- CVaR (95%): {metrics.cvar_95:.2%}")
            st.write(f"- Calmar Oranı: {metrics.calmar_ratio:.2f}")

        with col2:
            st.markdown("**İşlem İstatistikleri**")
            st.write(f"- Profit Factor: {metrics.profit_factor:.2f}")
            st.write(f"- Ortalama Kazanç: {metrics.avg_win:.2%}")
            st.write(f"- Ortalama Kayıp: {metrics.avg_loss:.2%}")
            st.write(f"- En İyi İşlem: {metrics.best_trade:.2%}")

    # Monte Carlo Results
    st.markdown("### 🎲 Monte Carlo Simülasyonu")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Beklenen Değer",
            f"${mc_result.mean_equity:,.0f}",
            delta=f"±${mc_result.std_equity:,.0f}",
        )

    with col2:
        prob_loss_color = (
            "green"
            if mc_result.prob_loss < 0.3
            else ("orange" if mc_result.prob_loss < 0.5 else "red")
        )
        st.metric(
            "Zarar Olasılığı",
            f"{mc_result.prob_loss:.1%}",
            delta=f"Yıkım: {mc_result.prob_ruin:.1%}",
            delta_color="inverse",
        )

    with col3:
        st.metric(
            "95. Percentile",
            f"${mc_result.equity_95th:,.0f}",
            delta=f"5th: ${mc_result.equity_5th:,.0f}",
        )

    # Walk-Forward Results (if available)
    if wf_summary:
        st.markdown("### 🔄 Walk-Forward Analizi")

        robust = wf_summary.get("robust", False)
        if robust:
            st.success("✅ Strateji ROBUST - Overfitting riski düşük")
        else:
            st.warning("⚠️ Overfitting riski tespit edildi")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Train Sharpe:** {wf_summary.get('avg_train_sharpe', 0):.2f}")
        with col2:
            st.write(f"**Test Sharpe:** {wf_summary.get('avg_test_sharpe', 0):.2f}")
        with col3:
            degradation = wf_summary.get("sharpe_degradation", 0)
            st.write(f"**Degradasyon:** {degradation:.1%}")

    # Generate Report Button
    st.markdown("---")
    if st.button("📄 HTML Rapor Oluştur", type="secondary"):
        try:
            report = create_report(
                metrics,
                strategy_name=f"{results['symbol']} {results['strategy']}",
                monte_carlo=mc_result.to_dict(),
                walk_forward=wf_summary,
                period_start=str(datetime.now().date()),
                period_end=str(datetime.now().date()),
            )

            gen = HTMLReportGenerator(ReportConfig(output_dir="reports"))
            path = gen.save(report)

            st.success(f"Rapor oluşturuldu: {path}")

            # Provide download link
            with open(path, "r") as f:
                html_content = f.read()

            st.download_button(
                "📥 Raporu İndir", html_content, file_name="backtest_report.html", mime="text/html"
            )
        except Exception as e:
            st.error(f"Rapor oluşturulamadı: {e}")


def render_history_page():
    """Ana performans analizi sayfası."""
    st.markdown("# 📊 FinPilot Performans Analizi")

    # Tabs for different sections
    tab1, tab2 = st.tabs(["🧪 Gelişmiş Backtest", "📜 Sinyal Geçmişi"])

    with tab1:
        render_backtest_section()

    with tab2:
        render_signal_history()


def render_signal_history():
    """Render historical signal log."""
    st.markdown("## 🚦 Strateji, Risk ve Getiri Analizi")

    signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")

    if os.path.exists(signal_log_path):
        try:
            log_df = pd.read_csv(signal_log_path, header=None)

            if log_df.empty:
                st.info("Sinyal günlüğü boş.")
                return

            expected_cols = [
                "Tarih",
                "Sembol",
                "Fiyat",
                "Stop-Loss",
                "Take-Profit",
                "Skor",
                "Güç",
                "Rejim",
                "Sentiment",
                "Onchain",
                "Alım?",
                "Özet",
                "Neden",
            ]

            if len(log_df.columns) == len(expected_cols):
                log_df.columns = expected_cols
            else:
                st.warning(
                    f"Sinyal günlüğü formatı beklenenden farklı ({len(log_df.columns)} sütun)."
                )

            # Filters
            col1, col2, col3 = st.columns([2, 2, 2])
            unique_dates = sorted(log_df["Tarih"].astype(str).unique().tolist(), reverse=True)
            selected_date = col1.selectbox("Tarih Seç", ["Tümü"] + unique_dates)

            unique_symbols = sorted(log_df["Sembol"].astype(str).unique().tolist())
            selected_symbol = col2.selectbox("Sembol Seç", ["Tümü"] + unique_symbols)

            regime_options = sorted(log_df["Rejim"].astype(str).unique().tolist())
            selected_regime = col3.selectbox("Rejim Filtrele", ["Tümü"] + regime_options)

            filtered = log_df.copy()
            if selected_date != "Tümü":
                filtered = filtered[filtered["Tarih"].astype(str) == selected_date]
            if selected_symbol != "Tümü":
                filtered = filtered[filtered["Sembol"] == selected_symbol]
            if selected_regime != "Tümü":
                filtered = filtered[filtered["Rejim"] == selected_regime]

            # Ensure numeric columns
            for col in ["Fiyat", "Stop-Loss", "Take-Profit", "Skor"]:
                if col in filtered.columns:
                    filtered[col] = pd.to_numeric(filtered[col], errors="coerce")

            # Calculate metrics
            avg_gain = (
                (filtered["Take-Profit"] - filtered["Fiyat"]).mean() if len(filtered) > 0 else 0
            )
            cagr = (
                ((filtered["Take-Profit"] / filtered["Fiyat"]).mean() - 1) * 100
                if len(filtered) > 0
                else 0
            )
            take_profit_mean = filtered["Take-Profit"].mean() if len(filtered) > 0 else 0

            avg_loss = (
                (filtered["Fiyat"] - filtered["Stop-Loss"]).mean() if len(filtered) > 0 else 0
            )
            rr_ratio = avg_gain / avg_loss if avg_loss != 0 else 0
            kelly = (rr_ratio - (1 - rr_ratio)) / rr_ratio if rr_ratio > 0 else 0
            max_drawdown = avg_loss

            total_signals = len(filtered)
            if "Alım?" in filtered.columns:
                is_buy = (
                    filtered["Alım?"]
                    .astype(str)
                    .str.lower()
                    .isin(["true", "1", "evet", "yes", "al"])
                )
                success_signals = is_buy.sum()
            else:
                success_signals = 0

            win_rate = (success_signals / total_signals * 100) if total_signals > 0 else 0
            avg_score = filtered["Skor"].mean() if total_signals > 0 else 0

            # Display metrics
            st.markdown("### 🚦 Risk/Ödül Kartı")
            rr_color = "#10b981" if rr_ratio >= 2 else ("#f59e42" if rr_ratio >= 1 else "#ef4444")
            st.markdown(
                f"<div style='background:{rr_color};color:#fff;padding:16px;border-radius:12px;font-size:1.3em;font-weight:bold;'>"
                f"R/R Oranı: {rr_ratio:.2f} | Maksimum Kayıp: {max_drawdown:.2f} | Kelly: {kelly:.2f}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("### 📈 Getiri & Hedefleme")
            st.markdown(f"Hedef Getiri: %{take_profit_mean:.2f} | CAGR: %{cagr:.2f}")

            st.markdown("### 🤖 Strateji & Uyum")
            st.markdown(
                f"Başarı Oranı (Win Rate): %{win_rate:.1f} | Ortalama Skor: {avg_score:.2f}"
            )

            st.dataframe(filtered, use_container_width=True)

        except Exception as e:
            st.error(f"Geçmiş sinyaller yüklenirken hata oluştu: {e}")
    else:
        st.info("Henüz geçmiş sinyal kaydı bulunmamaktadır.")
        st.caption("Tarama yaptıktan sonra sinyaller burada görünecektir.")
