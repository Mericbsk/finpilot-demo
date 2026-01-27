import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from views.components.stock_presets import STOCK_PRESETS
from views.translations import ACADEMY_TERMS, DEFAULT_TERM, STOCK_INSIGHTS, TRANSLATIONS

# Configure logger
logger = logging.getLogger(__name__)

# Standart TTL: 300 saniye (tüm modüllerle uyumlu)
DEMO_CACHE_TTL = 300


@st.cache_data(ttl=DEMO_CACHE_TTL)
def get_stock_history(symbol, period="6mo"):
    """Seçilen hisse için geçmiş verileri çeker (Cache: 5dk)."""
    try:
        hist = yf.Ticker(symbol).history(period=period)
        if hist is None or hist.empty:
            logger.warning("Hisse verisi alınamadı: %s", symbol)
            return pd.DataFrame()
        return hist
    except ConnectionError as e:
        logger.error("Hisse verisi bağlantı hatası: %s - %s", symbol, e)
        return pd.DataFrame()
    except Exception as e:
        logger.error("Hisse verisi beklenmeyen hata: %s - %s", symbol, e)
        return pd.DataFrame()


def calculate_indicators(df):
    """Basit teknik indikatörleri hesaplar (RSI, SMA, Bollinger, MACD)."""
    if df.empty or len(df) < 50:
        return None

    # RSI (14)
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # SMA 50 & 200
    df["SMA50"] = df["Close"].rolling(window=50).mean()
    df["SMA200"] = df["Close"].rolling(window=200).mean()

    # Bollinger Bands (20)
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["STD20"] = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = df["SMA20"] + (df["STD20"] * 2)
    df["BB_Lower"] = df["SMA20"] - (df["STD20"] * 2)

    # MACD (12, 26, 9)
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    return df


def calculate_ai_score(df):
    """Verilen veri setine göre 0-100 arası bir AI skoru ve sinyal üretir."""
    if df is None or df.empty:
        return 50, "NÖTR", "➡️"

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    score = 50  # Başlangıç skoru

    # 1. Trend (SMA50 vs SMA200) - 20 Puan
    if last_row["SMA50"] > last_row["SMA200"]:
        score += 10
        if last_row["Close"] > last_row["SMA50"]:
            score += 10
    else:
        score -= 10
        if last_row["Close"] < last_row["SMA50"]:
            score -= 10

    # 2. RSI (Momentum) - 20 Puan
    rsi = last_row["RSI"]
    if 50 < rsi < 70:
        score += 10
        if rsi > prev_row["RSI"]:  # RSI artıyor
            score += 10
    elif rsi > 70:  # Aşırı alım
        score -= 5
    elif rsi < 30:  # Aşırı satım (tepki ihtimali)
        score += 5
    elif rsi < 50:
        score -= 10

    # 3. MACD (Trend Gücü) - 20 Puan
    if last_row["MACD"] > last_row["MACD_Signal"]:
        score += 10
        if last_row["MACD_Hist"] > 0 and last_row["MACD_Hist"] > prev_row["MACD_Hist"]:
            score += 10
    else:
        score -= 10

    # 4. Bollinger Bands (Volatilite/Fırsat) - 20 Puan
    if last_row["Close"] < last_row["BB_Lower"]:  # Alım fırsatı olabilir
        score += 15
    elif last_row["Close"] > last_row["BB_Upper"]:  # Satış baskısı olabilir
        score -= 10
    elif last_row["Close"] > last_row["SMA20"]:  # Orta bandın üstünde
        score += 5

    # 5. Son Gün Performansı - 20 Puan
    change = (last_row["Close"] - prev_row["Close"]) / prev_row["Close"]
    if change > 0:
        score += 10
        if change > 0.02:  # %2'den fazla artış
            score += 10
    else:
        score -= 10

    # Skor Normalizasyonu (0-100)
    score = max(0, min(100, score))

    # Sinyal Belirleme
    if score >= 80:
        signal = "GÜÇLÜ AL"
        trend = "🚀"
    elif score >= 60:
        signal = "AL"
        trend = "↗️"
    elif score <= 20:
        signal = "GÜÇLÜ SAT"
        trend = "🔻"
    elif score <= 40:
        signal = "SAT"
        trend = "↘️"
    else:
        signal = "TUT"
        trend = "➡️"

    return score, signal, trend


@st.cache_data(ttl=DEMO_CACHE_TTL)
def get_live_market_data():
    """Canlı piyasa verilerini çeker, hata olursa mock veri döner."""
    indices = {"NASDAQ 100": "^NDX", "S&P 500": "^GSPC", "VIX": "^VIX"}

    market_data = {
        "NASDAQ 100": {"value": "19,500", "delta": "+1.2%"},
        "S&P 500": {"value": "5,600", "delta": "+0.8%"},
        "VIX": {"value": "13.5", "delta": "-2.1%"},
    }

    try:
        tickers = list(indices.values())
        data = yf.download(tickers, period="5d", progress=False, auto_adjust=False)["Close"]

        if not data.empty:
            # NASDAQ
            ndx_curr = data["^NDX"].iloc[-1]
            ndx_prev = data["^NDX"].iloc[-2]
            ndx_chg = ((ndx_curr - ndx_prev) / ndx_prev) * 100
            market_data["NASDAQ 100"] = {"value": f"{ndx_curr:,.0f}", "delta": f"{ndx_chg:+.2f}%"}

            # S&P 500
            spx_curr = data["^GSPC"].iloc[-1]
            spx_prev = data["^GSPC"].iloc[-2]
            spx_chg = ((spx_curr - spx_prev) / spx_prev) * 100
            market_data["S&P 500"] = {"value": f"{spx_curr:,.0f}", "delta": f"{spx_chg:+.2f}%"}

            # VIX
            vix_curr = data["^VIX"].iloc[-1]
            vix_prev = data["^VIX"].iloc[-2]
            vix_chg = ((vix_curr - vix_prev) / vix_prev) * 100
            market_data["VIX"] = {"value": f"{vix_curr:.2f}", "delta": f"{vix_chg:+.2f}%"}
    except ConnectionError as e:
        logger.error("Piyasa verisi bağlantı hatası: %s", e)
    except Exception as e:
        logger.warning("Piyasa verisi çekilemedi (mock veri kullanılıyor): %s", e)

    return market_data


@st.cache_data(ttl=DEMO_CACHE_TTL)
def get_live_stock_data(symbols):
    """Hisse senetleri için canlı fiyat ve AI analizi yapar."""
    stock_data = {}

    try:
        # Toplu veri çekme (6 aylık - indikatörler için)
        data = yf.download(
            symbols, period="6mo", group_by="ticker", progress=False, auto_adjust=False
        )

        if data is None or data.empty:
            logger.warning("Hisse verileri alınamadı: %s", symbols)
            return stock_data

        for sym in symbols:
            try:
                # Ticker bazlı DataFrame al
                df = data[sym] if len(symbols) > 1 else data

                if df.empty:
                    continue

                # Son fiyat ve değişim
                curr = df["Close"].iloc[-1]
                prev = df["Close"].iloc[-2]
                chg = ((curr - prev) / prev) * 100

                # İndikatörleri ve AI Skorunu Hesapla
                df_tech = calculate_indicators(df.copy())
                score, signal, trend = calculate_ai_score(df_tech)

                stock_data[sym] = {
                    "price": curr,
                    "change": chg,
                    "score": score,
                    "signal": signal,
                    "trend": trend,
                }
            except Exception as e:
                print(f"Error processing {sym}: {e}")
                # Hata durumunda varsayılan değerler
                stock_data[sym] = {
                    "price": 0.0,
                    "change": 0.0,
                    "score": 50,
                    "signal": "NÖTR",
                    "trend": "➡️",
                }

    except Exception as e:
        print(f"Stock data fetch error: {e}")

    return stock_data


def render_demo_page():
    # Language Selector
    lang_options = {"English": "en", "Deutsch": "de", "Türkçe": "tr"}

    # Initialize session state for language if not exists
    if "language" not in st.session_state:
        st.session_state.language = "en"

    # Sidebar for language selection (or top right if preferred, but sidebar is cleaner)
    with st.sidebar:
        st.markdown("### 🌐 Language / Sprache / Dil")
        selected_lang_label = st.selectbox(
            "Select Language",
            options=list(lang_options.keys()),
            index=list(lang_options.values()).index(st.session_state.language),
        )
        st.session_state.language = lang_options[selected_lang_label]

    lang = st.session_state.language
    t = TRANSLATIONS[lang]

    st.markdown(
        f"""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #00e6e6;'>{t["page_title"]}</h1>
        <p style='color: #cbd5f5; font-size: 1.2em;'>{t["subtitle"]}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Live Data Fetching
    with st.spinner(t["loading_data"]):
        market_info = get_live_market_data()

        # Her kategoriden 10'ar hisse seç (toplam 80 hisse demo için çok - 5'er hisse alalım)
        # Kullanıcı seçtiği kategoriye göre farklı listeler gösteren bir sistem

        # Kategori seçici
        demo_categories = {
            "🔥 Popüler": ["tech_giants", "ai_leaders"],
            "💼 Sektörler": ["semiconductors", "finance_banks", "biotech_large"],
            "🎯 Tematik": ["ev_mobility", "cloud_saas", "crypto_blockchain"],
            "📈 Strateji": ["high_dividend", "growth_momentum", "value_picks"],
        }

        # Sidebar'da kategori seçimi
        selected_category = st.sidebar.selectbox(
            "🎯 Demo Kategorisi", list(demo_categories.keys()), index=0
        )

        # Seçilen kategoriden sembolleri al (her preset'ten 5'er tane)
        category_presets = demo_categories[selected_category]
        symbols = []
        for preset_key in category_presets:
            preset = STOCK_PRESETS.get(preset_key)
            if preset:
                symbols.extend(preset.symbols[:5])  # Her preset'ten ilk 5

        # Fazla varsa 10'a sınırla
        symbols = symbols[:10]

        stock_info = get_live_stock_data(symbols)

    # --- Adım 1: Piyasa Nabzı ---
    st.markdown(f"### {t['market_pulse']}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="NASDAQ 100",
            value=market_info["NASDAQ 100"]["value"],
            delta=market_info["NASDAQ 100"]["delta"],
        )
    with col2:
        st.metric(
            label="S&P 500",
            value=market_info["S&P 500"]["value"],
            delta=market_info["S&P 500"]["delta"],
        )
    with col3:
        st.metric(
            label=t["vix_name"],
            value=market_info["VIX"]["value"],
            delta=market_info["VIX"]["delta"],
            delta_color="inverse",
        )
    with col4:
        st.metric(label=t["ai_risk"], value=t["risk_high"], delta=t["risk_bull"])

    st.info(f"💡 **{t['ai_comment_title']}:** {t['ai_comment_text']}")

    st.markdown("---")

    # --- Adım 2: Fırsat Tarayıcı (Live Data) ---
    st.markdown(f"### {t['scanner_title']}")
    st.write(t["scanner_desc"])

    # Prepare DataFrame from live data
    demo_rows = []

    # Dinamik company map - yfinance'dan çek veya sembolü kullan
    company_map = {
        # Tech Giants
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet",
        "AMZN": "Amazon",
        "META": "Meta",
        "NVDA": "NVIDIA",
        "TSLA": "Tesla",
        "NFLX": "Netflix",
        "CRM": "Salesforce",
        "ORCL": "Oracle",
        "ADBE": "Adobe",
        "INTC": "Intel",
        # AI Leaders
        "PLTR": "Palantir",
        "AI": "C3.ai",
        "PATH": "UiPath",
        "SNOW": "Snowflake",
        "DDOG": "Datadog",
        "MDB": "MongoDB",
        "CRWD": "CrowdStrike",
        "ZS": "Zscaler",
        # Semiconductors
        "AMD": "AMD",
        "AVGO": "Broadcom",
        "QCOM": "Qualcomm",
        "TXN": "Texas Instruments",
        "MU": "Micron",
        "AMAT": "Applied Materials",
        "LRCX": "Lam Research",
        "KLAC": "KLA",
        "MRVL": "Marvell",
        "ON": "ON Semi",
        "ADI": "Analog Devices",
        # Finance
        "JPM": "JPMorgan",
        "BAC": "Bank of America",
        "WFC": "Wells Fargo",
        "GS": "Goldman Sachs",
        "MS": "Morgan Stanley",
        "C": "Citigroup",
        "USB": "US Bancorp",
        "PNC": "PNC",
        "V": "Visa",
        "MA": "Mastercard",
        "PYPL": "PayPal",
        "SQ": "Block",
        # Biotech
        "AMGN": "Amgen",
        "GILD": "Gilead",
        "REGN": "Regeneron",
        "VRTX": "Vertex",
        "MRNA": "Moderna",
        "BIIB": "Biogen",
        "ILMN": "Illumina",
        # EV & Mobility
        "RIVN": "Rivian",
        "LCID": "Lucid",
        "NIO": "NIO",
        "XPEV": "XPeng",
        "LI": "Li Auto",
        "F": "Ford",
        "GM": "GM",
        "TM": "Toyota",
        # Cloud SaaS
        "NOW": "ServiceNow",
        "WDAY": "Workday",
        "TEAM": "Atlassian",
        "OKTA": "Okta",
        "HUBS": "HubSpot",
        "ZM": "Zoom",
        "DOCU": "DocuSign",
        "TWLO": "Twilio",
        # Crypto
        "COIN": "Coinbase",
        "MSTR": "MicroStrategy",
        "MARA": "Marathon Digital",
        "RIOT": "Riot Platforms",
        "HUT": "Hut 8",
        "CLSK": "CleanSpark",
        # Dividend
        "JNJ": "Johnson & Johnson",
        "PG": "Procter & Gamble",
        "KO": "Coca-Cola",
        "PEP": "PepsiCo",
        "MCD": "McDonald's",
        "WMT": "Walmart",
        "HD": "Home Depot",
        # Value
        "BRK-B": "Berkshire",
        "CVX": "Chevron",
        "XOM": "Exxon",
        "VZ": "Verizon",
        "T": "AT&T",
        "IBM": "IBM",
        "CSCO": "Cisco",
        "ABBV": "AbbVie",
        # Growth
        "SHOP": "Shopify",
        "SQ": "Block",
        "ROKU": "Roku",
        "SPOT": "Spotify",
        "UBER": "Uber",
        "LYFT": "Lyft",
        "ABNB": "Airbnb",
        "DASH": "DoorDash",
    }

    for sym in symbols:
        # Veri yoksa varsayılan değerler
        default_data = {"price": 0, "change": 0, "score": 50, "signal": "NÖTR", "trend": "-"}
        data = stock_info.get(sym, default_data)

        # Translate signal if possible, or keep as is if it comes from backend (backend returns TR currently)
        # Ideally backend should return code, but for now let's map simple ones if needed or just display
        # The backend `calculate_ai_score` returns TR strings. We might want to map them.
        # For now, let's keep it simple and maybe map the column headers.

        # Mapping signals for display
        signal_map = {
            "GÜÇLÜ AL": t["strong_buy"],
            "AL": t["buy"],
            "NÖTR": t["neutral"],
            "SAT": t["sell"],
            "GÜÇLÜ SAT": t["strong_sell"],
            "TUT": t["hold"],
        }
        display_signal = signal_map.get(data["signal"], data["signal"])

        demo_rows.append(
            {
                t["col_symbol"]: sym,
                t["col_company"]: company_map.get(sym, sym),
                t["col_price"]: f"${data['price']:.2f}",
                t["col_change"]: f"%{data['change']:.2f}",
                t["col_score"]: data["score"],
                t["col_signal"]: display_signal,
                t["col_trend"]: data["trend"],
            }
        )

    df_demo = pd.DataFrame(demo_rows)

    st.dataframe(df_demo, hide_index=True)

    selected_symbol = st.selectbox(t["select_stock"], df_demo[t["col_symbol"]].tolist())
    # We need to find the original symbol from the selected row (which might have translated headers)
    # But the selectbox uses the column values, which are symbols (e.g. NVDA), so it's fine.

    # However, to get the data back from df_demo, we need to use the translated column name
    selected_data = df_demo[df_demo[t["col_symbol"]] == selected_symbol].iloc[0]

    st.markdown("---")

    # --- Adım 3: Detaylı Analiz (Enhanced) ---
    st.markdown(f"### 3. {selected_symbol} - {t['analysis_title']}")

    # Layout: Left (Chart & Tech), Right (AI Logic & Trade Setup)
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # --- Gelişmiş Grafik ve Teknik Analiz ---
        hist_df = get_stock_history(selected_symbol, period="6mo")
        df_tech = calculate_indicators(hist_df.copy()) if not hist_df.empty else None

        if df_tech is not None:
            # Plotly Candlestick Chart
            fig = go.Figure()

            # Candlestick
            fig.add_trace(
                go.Candlestick(
                    x=df_tech.index,
                    open=df_tech["Open"],
                    high=df_tech["High"],
                    low=df_tech["Low"],
                    close=df_tech["Close"],
                    name=selected_symbol,
                )
            )

            # SMA 50
            fig.add_trace(
                go.Scatter(
                    x=df_tech.index,
                    y=df_tech["SMA50"],
                    line=dict(color="orange", width=1),
                    name="SMA 50",
                )
            )

            # Bollinger Bands
            fig.add_trace(
                go.Scatter(
                    x=df_tech.index,
                    y=df_tech["BB_Upper"],
                    line=dict(color="gray", width=1, dash="dot"),
                    name="BB Upper",
                    showlegend=False,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df_tech.index,
                    y=df_tech["BB_Lower"],
                    line=dict(color="gray", width=1, dash="dot"),
                    name="BB Lower",
                    fill="tonexty",
                    fillcolor="rgba(128,128,128,0.1)",
                    showlegend=False,
                )
            )

            fig.update_layout(
                title=f"{selected_symbol} - {t['chart_title']}",
                yaxis_title=t["col_price"],
                xaxis_rangeslider_visible=False,
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(t["chart_error"])

        st.markdown(f"#### 🧠 {t['report_title']}")

        # Genişletilmiş AI Yorum Mantığı
        # Use imported STOCK_INSIGHTS

        # Seçilen sembol için insight al, yoksa varsayılanı kullan
        default_insight = {
            "summary": f"{selected_symbol} {t['default_summary']}",
            "catalyst": t["default_catalyst"],
            "risk": t["default_risk"],
        }

        insight = default_insight
        if selected_symbol and selected_symbol in STOCK_INSIGHTS:
            symbol_insights = STOCK_INSIGHTS[selected_symbol]
            insight = symbol_insights.get(lang, symbol_insights.get("en", default_insight))

        # Tabs for detailed analysis
        tab1, tab2, tab3 = st.tabs([t["tab_strategy"], t["tab_tech"], t["tab_fund"]])

        with tab1:
            # Daha görsel ve yapılandırılmış AI yorumu
            st.markdown(
                f"""
            <div style="background-color: rgba(0, 230, 230, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #00e6e6; margin-bottom: 15px;">
                <strong style="color: #00e6e6; font-size: 1.1em;">🤖 {t['main_scenario']}:</strong><br>
                <span style="color: #cbd5f5;">{insight['summary']}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.info(f"**🚀 {t['catalyst']}:**\n\n{insight['catalyst']}")
            with col_i2:
                st.warning(f"**⚠️ {t['risk_factor']}:**\n\n{insight['risk']}")

            st.markdown("---")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**🔑 {t['support_levels']}**")
                # Clean price string to float
                price_str = str(selected_data[t["col_price"]]).replace("$", "").replace(",", "")
                price_val = float(price_str)
                st.write(f"1. {t['support']}: ${(price_val * 0.98):.2f}")
                st.write(f"2. {t['support']}: ${(price_val * 0.95):.2f}")
            with c2:
                st.markdown(f"**🚀 {t['resistance_levels']}**")
                st.write(f"1. {t['resistance']}: ${(price_val * 1.05):.2f}")
                st.write(f"2. {t['resistance']}: ${(price_val * 1.10):.2f}")

        with tab2:
            if df_tech is not None:
                last_row = df_tech.iloc[-1]
                rsi_val = last_row["RSI"]
                sma50_val = last_row["SMA50"]
                price_val = last_row["Close"]

                rsi_signal = (
                    t["sig_overbought"]
                    if rsi_val > 70
                    else t["sig_oversold"] if rsi_val < 30 else t["sig_neutral"]
                )
                sma_signal = t["sig_trend_pos"] if price_val > sma50_val else t["sig_trend_neg"]

                tech_data = {
                    t["tech_indicator"]: ["RSI (14)", "SMA (50)", t["tech_bb"], t["tech_mom"]],
                    t["tech_value"]: [
                        f"{rsi_val:.1f}",
                        f"${sma50_val:.2f}",
                        t["val_inside"],
                        t["val_positive"],
                    ],
                    t["tech_signal"]: [rsi_signal, sma_signal, t["sig_neutral"], t["sig_buy"]],
                }
                st.table(pd.DataFrame(tech_data))
            else:
                st.write(t["tech_error"])

        with tab3:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric(t["news_sentiment"], t["positive"], "+0.8")
                st.caption(t["news_desc"])
            with col_s2:
                st.metric(t["social_vol"], t["high"], "+%12")
                st.caption(t["social_desc"])

            st.markdown(f"**📊 {t['fund_multiples']}**")
            st.progress(0.85, text=f"{t['growth_score']}: 8.5/10")
            st.progress(0.70, text=f"{t['profit_score']}: 7.0/10")

    with col_side:
        # Clean price for calculation
        price_str = str(selected_data[t["col_price"]]).replace("$", "").replace(",", "")
        price_val = float(price_str)

        st.markdown(
            f"""
        <div style='background-color: rgba(30, 41, 59, 0.8); padding: 20px; border-radius: 15px; border: 1px solid #334155;'>
            <h2 style='color: #00e6e6; margin-top:0;'>{selected_data[t['col_signal']]}</h2>
            <div style='font-size: 4em; font-weight: bold; color: #f8fafc;'>{selected_data[t['col_score']]}</div>
            <div style='color: #94a3b8;'>/ 100 {t['col_score']}</div>
            <hr style='border-color: #475569;'>
            <div style='margin-bottom: 10px;'>
                <span style='color: #cbd5f5;'>🎯 {t['target_price']}:</span>
                <span style='float: right; color: #4ade80; font-weight: bold;'>${(price_val * 1.15):.2f}</span>
            </div>
            <div style='margin-bottom: 10px;'>
                <span style='color: #cbd5f5;'>🛡️ {t['stop_loss']}:</span>
                <span style='float: right; color: #f87171; font-weight: bold;'>${(price_val * 0.95):.2f}</span>
            </div>
            <div style='margin-top: 20px;'>
                <button style='width: 100%; background-color: #00e6e6; color: #0f172a; border: none; padding: 10px; border-radius: 5px; font-weight: bold;'>{t['copy_plan']}</button>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.info(t["data_disclaimer"])

    # --- Adım 4: FinSense Entegrasyonu (Contextual) ---
    st.markdown("---")
    st.markdown(f"### 4. 🎓 {t['academy_title']}")

    # Use imported ACADEMY_TERMS
    term_data = DEFAULT_TERM[lang]

    if selected_symbol and selected_symbol in ACADEMY_TERMS:
        symbol_terms = ACADEMY_TERMS[selected_symbol]
        term_data = symbol_terms.get(lang, symbol_terms.get("en", DEFAULT_TERM[lang]))

    with st.container():
        col_edu_1, col_edu_2 = st.columns([1, 2])

        with col_edu_1:
            st.markdown(
                f"""
            <div style="background-color: #0f172a; padding: 20px; border-radius: 10px; border: 1px solid #334155; height: 100%;">
                <h3 style="color: #00e6e6; margin-top: 0;">📚 {term_data['term']}</h3>
                <p style="color: #cbd5f5;">{term_data['desc']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_edu_2:
            st.info(f"💡 **{t['why_important']}**\n\n{term_data['why']}")
            st.success(f"🚀 **{t['finpilot_diff']}**\n\n{term_data['pro_tip']}")

    # --- Adım 5: Call to Action ---
    st.markdown("---")
    st.markdown(
        f"""
    <div style='background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(30,41,59,1) 100%); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #334155;'>
        <h2 style='color: #f8fafc;'>{t['cta_title']}</h2>
        <p style='color: #cbd5f5; font-size: 1.1em; max-width: 600px; margin: 0 auto 20px auto;'>
            {t['cta_desc']}
        </p>
        <div style='display: flex; justify-content: center; gap: 20px;'>
            <button style='background-color: #00e6e6; color: #0f172a; border: none; padding: 12px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold;'>{t['btn_start']}</button>
            <button style='background-color: transparent; color: #00e6e6; border: 2px solid #00e6e6; padding: 12px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold;'>{t['btn_explore']}</button>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.write("")
    if st.button(f"⬅️ {t['btn_back']}"):
        st.session_state.show_demo = False
        st.rerun()
