import streamlit as st
import pandas as pd
import yfinance as yf
import talib as ta
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- Ayarlar ---
st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📈 Profesyonel Trading Dashboard")

# --- Kullanıcı Girdileri ---
symbol = st.sidebar.text_input("Sembol", value="AAPL")
lookback_days = st.sidebar.slider("Geçmiş Gün", 30, 180, 60)

# --- Veri Çekme ---
end = datetime.now()
start = end - timedelta(days=lookback_days)
df_15m = yf.download(symbol, start=start, end=end, interval="15m")
df_4h = yf.download(symbol, start=start, end=end, interval="4h")
df_1d = yf.download(symbol, start=start, end=end, interval="1d")

# --- Veri Kontrolü ---
if df_15m is None or df_4h is None or df_1d is None or df_15m.empty or df_4h.empty or df_1d.empty:
    st.error("Veri çekilemedi veya sembol hatalı. Lütfen geçerli bir sembol girin.")
    st.stop()

# --- İndikatörler ---
def add_indicators(df):
    df['ema50'] = ta.EMA(df['Close'].values, timeperiod=50)
    df['ema200'] = ta.EMA(df['Close'].values, timeperiod=200)
    df['rsi'] = ta.RSI(df['Close'].values, timeperiod=14)
    macd, macd_signal, macd_hist = ta.MACD(df['Close'].values, 12, 26, 9)
    df['macd'] = macd
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_hist
    upper, middle, lower = ta.BBANDS(df['Close'].values, timeperiod=20, nbdevup=2, nbdevdn=2)
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    df['atr'] = ta.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
    df['vol_med20'] = pd.Series(df['Volume']).rolling(20).median().values
    return df

df_15m = add_indicators(df_15m)
df_4h = add_indicators(df_4h)
df_1d = add_indicators(df_1d)

# --- Filtreler ---
regime_filter = df_1d['Close'].iloc[-1] > df_1d['ema200'].iloc[-1]
direction_filter = df_4h['Close'].iloc[-1] > df_4h['ema50'].iloc[-1]

# --- Sinyal Hesaplama ---
def signal_score(row):
    # Bu fonksiyon kaldırıldı, skorlar aşağıda hesaplanacak
    pass

df_15m['signal_score'] = 0
for i in range(1, len(df_15m)):
    score = 0
    if (
        df_15m['Close'].iloc[i] > df_15m['bb_lower'].iloc[i]
        and df_15m['Close'].iloc[i-1] < df_15m['bb_lower'].iloc[i-1]
    ):
        score += 1
    if (
        30 <= df_15m['rsi'].iloc[i] <= 45
        and df_15m['rsi'].iloc[i] > df_15m['rsi'].iloc[i-1]
    ):
        score += 1
    if (
        df_15m['macd_hist'].iloc[i] > 0
        and df_15m['macd_hist'].iloc[i-1] < 0
    ):
        score += 1
    if (
        df_15m['Volume'].iloc[i] >= df_15m['vol_med20'].iloc[i] * 1.2
    ):
        score += 1
    df_15m.at[df_15m.index[i], 'signal_score'] = score

# --- Son Sinyal ---
latest = df_15m.iloc[-1]
if regime_filter and direction_filter and latest['signal_score'] >= 2:
    st.success(f"📈 BUY sinyali | Skor: {latest['signal_score']}")
else:
    st.warning(f"⏳ Sinyal yok | Skor: {latest['signal_score']}")

# --- Grafik ---
fig = go.Figure(data=[go.Candlestick(
    x=df_15m.index,
    open=df_15m['Open'],
    high=df_15m['High'],
    low=df_15m['Low'],
    close=df_15m['Close'],
    name="Fiyat"
)])
fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['bb_upper'], line=dict(color='blue', width=1), name='BB Üst'))
fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['bb_lower'], line=dict(color='blue', width=1), name='BB Alt'))
st.plotly_chart(fig, use_container_width=True)

# --- Geçmiş Sinyaller ---
st.subheader("📜 Geçmiş Sinyaller")
signal_df = df_15m[df_15m['signal_score'] >= 2]
st.dataframe(signal_df[['Close', 'rsi', 'macd_hist', 'Volume', 'signal_score']].tail(20))
