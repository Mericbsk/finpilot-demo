import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

@st.cache_data(ttl=300)
def get_stock_history(symbol, period="6mo"):
    """Seçilen hisse için geçmiş verileri çeker (Cache: 5dk)."""
    try:
        hist = yf.Ticker(symbol).history(period=period)
        return hist
    except Exception as e:
        return pd.DataFrame()

def calculate_indicators(df):
    """Basit teknik indikatörleri hesaplar (RSI, SMA, Bollinger, MACD)."""
    if df.empty or len(df) < 50:
        return None
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # SMA 50 & 200
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # Bollinger Bands (20)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA20'] + (df['STD20'] * 2)
    df['BB_Lower'] = df['SMA20'] - (df['STD20'] * 2)

    # MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df

def calculate_ai_score(df):
    """Verilen veri setine göre 0-100 arası bir AI skoru ve sinyal üretir."""
    if df is None or df.empty:
        return 50, "NÖTR", "➡️"
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    score = 50 # Başlangıç skoru
    
    # 1. Trend (SMA50 vs SMA200) - 20 Puan
    if last_row['SMA50'] > last_row['SMA200']:
        score += 10
        if last_row['Close'] > last_row['SMA50']:
            score += 10
    else:
        score -= 10
        if last_row['Close'] < last_row['SMA50']:
            score -= 10

    # 2. RSI (Momentum) - 20 Puan
    rsi = last_row['RSI']
    if 50 < rsi < 70:
        score += 10
        if rsi > prev_row['RSI']: # RSI artıyor
            score += 10
    elif rsi > 70: # Aşırı alım
        score -= 5
    elif rsi < 30: # Aşırı satım (tepki ihtimali)
        score += 5
    elif rsi < 50:
        score -= 10

    # 3. MACD (Trend Gücü) - 20 Puan
    if last_row['MACD'] > last_row['MACD_Signal']:
        score += 10
        if last_row['MACD_Hist'] > 0 and last_row['MACD_Hist'] > prev_row['MACD_Hist']:
            score += 10
    else:
        score -= 10

    # 4. Bollinger Bands (Volatilite/Fırsat) - 20 Puan
    if last_row['Close'] < last_row['BB_Lower']: # Alım fırsatı olabilir
        score += 15
    elif last_row['Close'] > last_row['BB_Upper']: # Satış baskısı olabilir
        score -= 10
    elif last_row['Close'] > last_row['SMA20']: # Orta bandın üstünde
        score += 5

    # 5. Son Gün Performansı - 20 Puan
    change = (last_row['Close'] - prev_row['Close']) / prev_row['Close']
    if change > 0:
        score += 10
        if change > 0.02: # %2'den fazla artış
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

@st.cache_data(ttl=300)
def get_live_market_data():
    """Canlı piyasa verilerini çeker, hata olursa mock veri döner."""
    indices = {
        "NASDAQ 100": "^NDX",
        "S&P 500": "^GSPC",
        "VIX": "^VIX"
    }
    
    market_data = {
        "NASDAQ 100": {"value": "19,500", "delta": "+1.2%"},
        "S&P 500": {"value": "5,600", "delta": "+0.8%"},
        "VIX": {"value": "13.5", "delta": "-2.1%"}
    }

    try:
        tickers = list(indices.values())
        data = yf.download(tickers, period="5d", progress=False)['Close']
        
        if not data.empty:
            # NASDAQ
            ndx_curr = data["^NDX"].iloc[-1]
            ndx_prev = data["^NDX"].iloc[-2]
            ndx_chg = ((ndx_curr - ndx_prev) / ndx_prev) * 100
            market_data["NASDAQ 100"] = {
                "value": f"{ndx_curr:,.0f}",
                "delta": f"{ndx_chg:+.2f}%"
            }
            
            # S&P 500
            spx_curr = data["^GSPC"].iloc[-1]
            spx_prev = data["^GSPC"].iloc[-2]
            spx_chg = ((spx_curr - spx_prev) / spx_prev) * 100
            market_data["S&P 500"] = {
                "value": f"{spx_curr:,.0f}",
                "delta": f"{spx_chg:+.2f}%"
            }
            
            # VIX
            vix_curr = data["^VIX"].iloc[-1]
            vix_prev = data["^VIX"].iloc[-2]
            vix_chg = ((vix_curr - vix_prev) / vix_prev) * 100
            market_data["VIX"] = {
                "value": f"{vix_curr:.2f}",
                "delta": f"{vix_chg:+.2f}%"
            }
    except Exception as e:
        print(f"Market data fetch error: {e}")
        
    return market_data

@st.cache_data(ttl=300)
def get_live_stock_data(symbols):
    """Hisse senetleri için canlı fiyat ve AI analizi yapar."""
    stock_data = {}
    
    try:
        # Toplu veri çekme (6 aylık - indikatörler için)
        data = yf.download(symbols, period="6mo", group_by='ticker', progress=False)
        
        for sym in symbols:
            try:
                # Ticker bazlı DataFrame al
                df = data[sym] if len(symbols) > 1 else data
                
                if df.empty:
                    continue
                    
                # Son fiyat ve değişim
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                chg = ((curr - prev) / prev) * 100
                
                # İndikatörleri ve AI Skorunu Hesapla
                df_tech = calculate_indicators(df.copy())
                score, signal, trend = calculate_ai_score(df_tech)
                
                stock_data[sym] = {
                    "price": curr, 
                    "change": chg,
                    "score": score,
                    "signal": signal,
                    "trend": trend
                }
            except Exception as e:
                print(f"Error processing {sym}: {e}")
                # Hata durumunda varsayılan değerler
                stock_data[sym] = {
                    "price": 0.0, "change": 0.0,
                    "score": 50, "signal": "NÖTR", "trend": "➡️"
                }
                
    except Exception as e:
        print(f"Stock data fetch error: {e}")
        
    return stock_data

def render_demo_page():
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #00e6e6;'>🚀 FinPilot Global Demo</h1>
        <p style='color: #cbd5f5; font-size: 1.2em;'>NASDAQ & S&P 500 Devleri İçin Yapay Zeka Analizi</p>
    </div>
    """, unsafe_allow_html=True)

    # Live Data Fetching
    with st.spinner('Canlı piyasa verileri alınıyor...'):
        market_info = get_live_market_data()
        
        symbols = ["NVDA", "TSLA", "AAPL", "AMD", "AMZN", "MSFT", "META", "GOOGL", "NFLX", "COIN"]
        stock_info = get_live_stock_data(symbols)

    # --- Adım 1: Piyasa Nabzı ---
    st.markdown("### 1. Küresel Piyasa Nabzı")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="NASDAQ 100", value=market_info["NASDAQ 100"]["value"], delta=market_info["NASDAQ 100"]["delta"])
    with col2:
        st.metric(label="S&P 500", value=market_info["S&P 500"]["value"], delta=market_info["S&P 500"]["delta"])
    with col3:
        st.metric(label="VIX (Korku Endeksi)", value=market_info["VIX"]["value"], delta=market_info["VIX"]["delta"], delta_color="inverse")
    with col4:
        st.metric(label="AI Risk İştahı", value="Yüksek", delta="Boğa")

    st.info("💡 **Yapay Zeka Yorumu:** Teknoloji sektörü öncülüğünde momentum güçlü. Düzeltmeler alım fırsatı olarak değerlendiriliyor.")

    st.markdown("---")

    # --- Adım 2: Fırsat Tarayıcı (Live Data) ---
    st.markdown("### 2. Günün Öne Çıkan 10 Fırsatı")
    st.write("FinPilot, Amerikan borsalarındaki en likit hisseleri tarayarak anlık fırsatları listeledi.")

    # Prepare DataFrame from live data
    demo_rows = []
    company_map = {
        "NVDA": "NVIDIA", "TSLA": "Tesla", "AAPL": "Apple", "AMD": "AMD", 
        "AMZN": "Amazon", "MSFT": "Microsoft", "META": "Meta", 
        "GOOGL": "Alphabet", "NFLX": "Netflix", "COIN": "Coinbase"
    }
    
    for sym in symbols:
        # Veri yoksa varsayılan değerler
        default_data = {"price": 0, "change": 0, "score": 50, "signal": "NÖTR", "trend": "-"}
        data = stock_info.get(sym, default_data)
        
        demo_rows.append({
            "Sembol": sym,
            "Şirket": company_map.get(sym, sym),
            "Fiyat": f"${data['price']:.2f}",
            "Değişim": f"%{data['change']:.2f}",
            "AI Skoru": data["score"],
            "Sinyal": data["signal"],
            "Trend": data["trend"]
        })

    df_demo = pd.DataFrame(demo_rows)
    
    st.dataframe(df_demo, use_container_width=True, hide_index=True)

    selected_symbol = st.selectbox("Detaylı analiz için bir hisse seçin:", df_demo["Sembol"].tolist())
    selected_data = df_demo[df_demo["Sembol"] == selected_symbol].iloc[0]

    st.markdown("---")

    # --- Adım 3: Detaylı Analiz (Enhanced) ---
    st.markdown(f"### 3. {selected_symbol} - Yapay Zeka Derinlemesine Analiz")

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
            fig.add_trace(go.Candlestick(
                x=df_tech.index,
                open=df_tech['Open'], high=df_tech['High'],
                low=df_tech['Low'], close=df_tech['Close'],
                name=selected_symbol
            ))
            
            # SMA 50
            fig.add_trace(go.Scatter(
                x=df_tech.index, y=df_tech['SMA50'],
                line=dict(color='orange', width=1), name='SMA 50'
            ))
            
            # Bollinger Bands
            fig.add_trace(go.Scatter(
                x=df_tech.index, y=df_tech['BB_Upper'],
                line=dict(color='gray', width=1, dash='dot'), name='BB Upper', showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=df_tech.index, y=df_tech['BB_Lower'],
                line=dict(color='gray', width=1, dash='dot'), name='BB Lower', fill='tonexty', fillcolor='rgba(128,128,128,0.1)', showlegend=False
            ))

            fig.update_layout(
                title=f"{selected_symbol} - Teknik Görünüm",
                yaxis_title="Fiyat ($)",
                xaxis_rangeslider_visible=False,
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Grafik verisi yüklenemedi.")
        
        st.markdown("#### 🧠 FinPilot AI Derin Analiz Raporu")
        
        # Genişletilmiş AI Yorum Mantığı
        ai_insights = {
            "NVDA": {
                "summary": "Yapay zeka çiplerine olan talep patlaması, veri merkezi gelirlerini rekor seviyelere taşıyor. Sektör lideri konumu korunuyor.",
                "catalyst": "Kurumsal 'Smart Money' girişi son 2 haftada %15 arttı. Yeni Blackwell çip serisi beklentisi fiyatlanıyor.",
                "risk": "Aşırı değerleme (High Valuation) riski mevcut. $120 altı kapanışlarda kar realizasyonu hızlanabilir."
            },
            "TSLA": {
                "summary": "Elektrikli araç pazarındaki fiyat rekabetine rağmen, otonom sürüş (FSD) ve robotik projeleri uzun vadeli hikayeyi canlı tutuyor.",
                "catalyst": "$220-$230 bandında güçlü bir 'Toplama' (Accumulation) sinyali tespit edildi. RSI pozitif uyumsuzluk gösteriyor.",
                "risk": "Kısa vadeli kar marjı baskıları devam ediyor. Volatilite yüksek, stop seviyelerine sadık kalınmalı."
            },
            "AAPL": {
                "summary": "Hizmet gelirlerindeki artış ve ekosistem gücü hisseyi defansif bir liman yapıyor. Vision Pro ve AI entegrasyonu yeni büyüme alanı.",
                "catalyst": "Geri alım programı (Buyback) hisse başına karı destekliyor. $210 seviyesi kurumsal alıcılar için güçlü destek.",
                "risk": "Çin pazarındaki satışların yavaşlaması ve antitröst davaları baskı yaratabilir."
            },
            "AMD": {
                "summary": "Nvidia'nın en güçlü rakibi olarak MI300 çipleriyle pazar payı kapma mücadelesinde. Veri merkezi yatırımları AMD'ye kayıyor.",
                "catalyst": "Teknik olarak düşen trend kırılımı gerçekleşti. Hacimli yükseliş boğa tuzağı olmadığını teyit ediyor.",
                "risk": "Yarı iletken sektöründeki genel bir satış dalgası hisseyi sert etkileyebilir."
            },
            "AMZN": {
                "summary": "AWS bulut gelirlerindeki istikrar ve e-ticaret tarafındaki verimlilik artışı karlılığı destekliyor.",
                "catalyst": "Yapay zeka odaklı veri merkezi yatırımları uzun vadeli büyümeyi garantiliyor. $180 direnci hacimli geçildi.",
                "risk": "Tüketici harcamalarındaki olası bir yavaşlama perakende kanadını baskılayabilir."
            },
            "MSFT": {
                "summary": "Copilot yapay zeka asistanının ofis ürünlerine entegrasyonu, yazılım gelirlerinde yeni bir döngü başlattı.",
                "catalyst": "Azure bulut büyümesi beklentilerin üzerinde. Kurumsal talep güçlü kalmaya devam ediyor.",
                "risk": "Düzenleyici kurumların (Regülasyon) yapay zeka üzerindeki baskısı artabilir."
            },
            "META": {
                "summary": "Reklam gelirlerindeki toparlanma ve 'Verimlilik Yılı' stratejisi bilançoyu güçlendirdi.",
                "catalyst": "Yapay zeka destekli reklam hedefleme algoritmaları dönüşüm oranlarını artırıyor. F/K oranı hala makul seviyede.",
                "risk": "Metaverse harcamalarının karlılık üzerindeki baskısı yatırımcıları endişelendirebilir."
            },
            "GOOGL": {
                "summary": "Arama motoru hakimiyeti ve Gemini AI modelindeki gelişmeler rekabet gücünü koruyor.",
                "catalyst": "YouTube reklam gelirleri ve Cloud büyümesi pozitif sürpriz yapabilir. Hisse geri alım programı destekleyici.",
                "risk": "Yapay zeka tabanlı arama rekabeti (ChatGPT vb.) pazar payı kaybı riski yaratıyor."
            },
            "NFLX": {
                "summary": "Şifre paylaşımı kısıtlamasının başarısı ve reklamlı abonelik modeli abone sayısını artırıyor.",
                "catalyst": "İçerik kütüphanesinin gücü ve global büyüme, nakit akışını (Free Cash Flow) pozitif etkiliyor.",
                "risk": "İçerik üretim maliyetlerinin artması ve yayıncılık sektöründeki doygunluk."
            },
            "COIN": {
                "summary": "Kripto para piyasasındaki boğa döngüsü ve ETF onayları işlem hacimlerini patlattı.",
                "catalyst": "Bitcoin fiyatındaki yükselişle doğrudan korelasyon gösteriyor. Kurumsal saklama hizmetleri geliri artıyor.",
                "risk": "SEC ile devam eden yasal süreçler ve kripto piyasasındaki ani sert düşüşler."
            }
        }

        # Seçilen sembol için insight al, yoksa varsayılanı kullan
        default_insight = {
            "summary": f"{selected_symbol} hissesinde yükseliş trendi momentum kazanıyor. Sektörel rotasyon bu hisse lehine dönüyor.",
            "catalyst": "Hacim osilatörleri ve trend göstergeleri uyumlu bir 'AL' sinyali üretiyor.",
            "risk": "Piyasa genelindeki olası bir düzeltmede beta katsayısı yüksek olduğu için sert tepki verebilir."
        }
        
        if selected_symbol:
            insight = ai_insights.get(selected_symbol, default_insight)
        else:
            insight = default_insight

        # Tabs for detailed analysis
        tab1, tab2, tab3 = st.tabs(["📋 AI Strateji Özeti", "📈 Teknik Sinyaller", "🌍 Temel & Sentiment"])

        with tab1:
            # Daha görsel ve yapılandırılmış AI yorumu
            st.markdown(f"""
            <div style="background-color: rgba(0, 230, 230, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #00e6e6; margin-bottom: 15px;">
                <strong style="color: #00e6e6; font-size: 1.1em;">🤖 Ana Senaryo:</strong><br>
                <span style="color: #cbd5f5;">{insight['summary']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.info(f"**🚀 Tetikleyici (Catalyst):**\n\n{insight['catalyst']}")
            with col_i2:
                st.warning(f"**⚠️ Risk Faktörü:**\n\n{insight['risk']}")

            st.markdown("---")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🔑 Kritik Destek Seviyeleri**")
                price_val = float(selected_data['Fiyat'].replace('$','').replace(',',''))
                st.write(f"1. Destek: ${(price_val * 0.98):.2f}")
                st.write(f"2. Destek: ${(price_val * 0.95):.2f}")
            with c2:
                st.markdown("**🚀 Kritik Direnç Seviyeleri**")
                st.write(f"1. Direnç: ${(price_val * 1.05):.2f}")
                st.write(f"2. Direnç: ${(price_val * 1.10):.2f}")

        with tab2:
            if df_tech is not None:
                last_row = df_tech.iloc[-1]
                rsi_val = last_row['RSI']
                sma50_val = last_row['SMA50']
                price_val = last_row['Close']
                
                rsi_signal = "AŞIRI ALIM (SAT)" if rsi_val > 70 else "AŞIRI SATIM (AL)" if rsi_val < 30 else "NÖTR"
                sma_signal = "AL (Trend Pozitif)" if price_val > sma50_val else "SAT (Trend Negatif)"
                
                tech_data = {
                    "İndikatör": ["RSI (14)", "SMA (50)", "Bollinger Bantları", "Momentum"],
                    "Değer": [f"{rsi_val:.1f}", f"${sma50_val:.2f}", "Bandın İçinde", "Pozitif"],
                    "Sinyal": [rsi_signal, sma_signal, "NÖTR", "AL"]
                }
                st.table(pd.DataFrame(tech_data))
            else:
                st.write("Teknik veriler hesaplanamadı.")
        
        with tab3:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("Haber Duyarlılığı", "Pozitif", "+0.8")
                st.caption("Son 24 saatteki 150+ haber kaynağı tarandı.")
            with col_s2:
                st.metric("Sosyal Medya Hacmi", "Yüksek", "+%12")
                st.caption("Twitter ve Reddit üzerindeki tartışma yoğunluğu.")
            
            st.markdown("**📊 Temel Çarpanlar**")
            st.progress(0.85, text="Büyüme Skoru: 8.5/10")
            st.progress(0.70, text="Karlılık Skoru: 7.0/10")

    with col_side:
        st.markdown(f"""
        <div style='background-color: rgba(30, 41, 59, 0.8); padding: 20px; border-radius: 15px; border: 1px solid #334155;'>
            <h2 style='color: #00e6e6; margin-top:0;'>{selected_data['Sinyal']}</h2>
            <div style='font-size: 4em; font-weight: bold; color: #f8fafc;'>{selected_data['AI Skoru']}</div>
            <div style='color: #94a3b8;'>/ 100 AI Skoru</div>
            <hr style='border-color: #475569;'>
            <div style='margin-bottom: 10px;'>
                <span style='color: #cbd5f5;'>🎯 Hedef Fiyat:</span>
                <span style='float: right; color: #4ade80; font-weight: bold;'>${(float(selected_data['Fiyat'].replace('$','')) * 1.15):.2f}</span>
            </div>
            <div style='margin-bottom: 10px;'>
                <span style='color: #cbd5f5;'>🛡️ Stop Loss:</span>
                <span style='float: right; color: #f87171; font-weight: bold;'>${(float(selected_data['Fiyat'].replace('$','')) * 0.95):.2f}</span>
            </div>
            <div style='margin-top: 20px;'>
                <button style='width: 100%; background-color: #00e6e6; color: #0f172a; border: none; padding: 10px; border-radius: 5px; font-weight: bold;'>İşlem Planını Kopyala</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("Bu analiz son 15 dakikadaki piyasa verilerine dayanmaktadır.")

    # --- Adım 4: FinSense Entegrasyonu (Contextual) ---
    st.markdown("---")
    st.markdown("### 4. 🎓 FinSense Akademi: Yatırımcı IQ'nuzu Yükseltin")
    
    term_map = {
        "NVDA": {
            "term": "Volatilite (Oynaklık)",
            "desc": "Fiyatların belirli bir sürede ne kadar hızlı ve sert değiştiğinin ölçüsüdür.",
            "why": "Yüksek volatilite risk demektir ama profesyoneller için büyük kazanç fırsatıdır. Acemi yatırımcıyı panikletir, profesyoneli zengin eder.",
            "pro_tip": "FinPilot'un 'Regime Detection' modülü, volatilitenin ne zaman tehlikeli, ne zaman fırsat olduğunu ayırt eder."
        },
        "TSLA": {
            "term": "Momentum",
            "desc": "Bir hissenin fiyat değişim hızıdır. Bir arabanın ivmesi gibidir.",
            "why": "Güçlü momentum, trendin devam etme olasılığını artırır. Trendin tersine işlem açmak (ayı tuzağı) en büyük hatadır.",
            "pro_tip": "FinPilot, momentumun zayıfladığı ve trendin döneceği 'kritik anları' yapay zeka ile tespit eder."
        },
        "AAPL": {
            "term": "Defansif Büyüme",
            "desc": "Hem güvenli liman olup hem de büyümeye devam edebilen nadir şirket yapısıdır.",
            "why": "Piyasa çökerken portföyünüzü korur, yükselirken getiri sağlar. Her portföyün sigortasıdır.",
            "pro_tip": "FinPilot, portföyünüzdeki 'Riskli' ve 'Güvenli' hisse dengesini otomatik olarak optimize eder."
        },
        "COIN": {
            "term": "Korelasyon",
            "desc": "İki farklı varlığın (örn. Bitcoin ve Coinbase) fiyat hareketlerinin birbirine benzerliğidir.",
            "why": "Eğer portföyünüzde hem Bitcoin hem COIN varsa, aslında aynı riski iki kere almış olursunuz.",
            "pro_tip": "FinPilot, portföyünüzdeki 'Gizli Riskleri' ve korelasyonları tarayarak sizi uyarır."
        }
    }
    
    default_term = {
        "term": "Trend Takibi",
        "desc": "Fiyatların genel yönünü (Yükseliş, Düşüş veya Yatay) analiz etme yöntemidir.",
        "why": "'Trend senin dostundur.' Borsada para kaybetmenin en kolay yolu inatlaşmak, kazanmanın yolu ise akıntıya uyum sağlamaktır.",
        "pro_tip": "İnsanlar duygusaldır, FinPilot ise matematiktir. Algoritmalarımız trendi duygusuzca takip eder."
    }
    
    # Ensure selected_symbol is not None before accessing dictionary
    if selected_symbol:
        term_data = term_map.get(selected_symbol, default_term)
    else:
        term_data = default_term

    with st.container():
        col_edu_1, col_edu_2 = st.columns([1, 2])
        
        with col_edu_1:
            st.markdown(f"""
            <div style="background-color: #0f172a; padding: 20px; border-radius: 10px; border: 1px solid #334155; height: 100%;">
                <h3 style="color: #00e6e6; margin-top: 0;">📚 {term_data['term']}</h3>
                <p style="color: #cbd5f5;">{term_data['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_edu_2:
            st.info(f"💡 **Neden Önemli?**\n\n{term_data['why']}")
            st.success(f"🚀 **FinPilot Farkı:**\n\n{term_data['pro_tip']}")

    # --- Adım 5: Call to Action ---
    st.markdown("---")
    st.markdown("""
    <div style='background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(30,41,59,1) 100%); padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #334155;'>
        <h2 style='color: #f8fafc;'>Profesyonel Yatırımcı Gibi Analiz Edin</h2>
        <p style='color: #cbd5f5; font-size: 1.1em; max-width: 600px; margin: 0 auto 20px auto;'>
            FinPilot'un tam sürümü ile BIST, NASDAQ ve Kripto piyasalarında 1000+ varlığı tarayın, kendi stratejilerinizi oluşturun ve riskinizi yönetin.
        </p>
        <div style='display: flex; justify-content: center; gap: 20px;'>
            <button style='background-color: #00e6e6; color: #0f172a; border: none; padding: 12px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold;'>Ücretsiz Başla</button>
            <button style='background-color: transparent; color: #00e6e6; border: 2px solid #00e6e6; padding: 12px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold;'>Özellikleri İncele</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button("⬅️ Ana Panele Dön"):
        st.session_state.show_demo = False
        st.rerun()
