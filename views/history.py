import os
import pandas as pd
import streamlit as st

def render_history_page():
    st.markdown("#  FinPilot Performans Analizi")
    signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
    st.markdown("## 🚦 Strateji, Risk ve Getiri Analizi")
    if os.path.exists(signal_log_path):
        try:
            log_df = pd.read_csv(signal_log_path, header=None)
            # Check if dataframe is empty or has enough columns
            if log_df.empty:
                st.info("Sinyal günlüğü boş.")
                return
                
            # Adjust columns based on actual data width if needed, but assuming standard format
            expected_cols = [
                "Tarih", "Sembol", "Fiyat", "Stop-Loss", "Take-Profit", "Skor", "Güç", "Rejim", "Sentiment", "Onchain", "Alım?", "Özet", "Neden"
            ]
            if len(log_df.columns) == len(expected_cols):
                log_df.columns = expected_cols
            else:
                # Fallback or partial mapping could be done here
                st.warning(f"Sinyal günlüğü formatı beklenenden farklı ({len(log_df.columns)} sütun).")
                
            # Filtreler
            col1, col2, col3 = st.columns([2,2,2])
            unique_dates = sorted(log_df['Tarih'].astype(str).unique().tolist(), reverse=True)
            selected_date = col1.selectbox("Tarih Seç", ["Tümü"] + unique_dates)
            
            unique_symbols = sorted(log_df['Sembol'].astype(str).unique().tolist())
            selected_symbol = col2.selectbox("Sembol Seç", ["Tümü"] + unique_symbols)
            
            regime_options = sorted(log_df['Rejim'].astype(str).unique().tolist())
            selected_regime = col3.selectbox("Rejim Filtrele", ["Tümü"] + regime_options)

            filtered = log_df.copy()
            if selected_date != "Tümü":
                filtered = filtered[filtered['Tarih'].astype(str) == selected_date]
            if selected_symbol != "Tümü":
                filtered = filtered[filtered['Sembol'] == selected_symbol]
            if selected_regime != "Tümü":
                filtered = filtered[filtered['Rejim'] == selected_regime]

            # 1. Getiri & Hedefleme
            # Ensure numeric columns are numeric
            for col in ['Fiyat', 'Stop-Loss', 'Take-Profit', 'Skor']:
                if col in filtered.columns:
                    filtered[col] = pd.to_numeric(filtered[col], errors='coerce')

            avg_gain = (filtered['Take-Profit'] - filtered['Fiyat']).mean() if len(filtered) > 0 else 0
            cagr = ((filtered['Take-Profit'] / filtered['Fiyat']).mean() - 1) * 100 if len(filtered) > 0 else 0
            take_profit_mean = filtered['Take-Profit'].mean() if len(filtered) > 0 else 0

            # 2. Risk & Uçurum
            avg_loss = (filtered['Fiyat'] - filtered['Stop-Loss']).mean() if len(filtered) > 0 else 0
            rr_ratio = avg_gain / avg_loss if avg_loss != 0 else 0
            kelly = (rr_ratio - (1 - rr_ratio)) / rr_ratio if rr_ratio > 0 else 0
            max_drawdown = avg_loss # örnek, daha gelişmiş hesaplama eklenebilir

            # 3. Strateji & Uyum
            total_signals = len(filtered)
            # Handle boolean column for 'Alım?'
            if 'Alım?' in filtered.columns:
                is_buy = filtered['Alım?'].astype(str).str.lower().isin(['true', '1', 'evet', 'yes', 'al'])
                success_signals = is_buy.sum()
            else:
                success_signals = 0
                
            win_rate = (success_signals / total_signals * 100) if total_signals > 0 else 0
            avg_score = filtered['Skor'].mean() if total_signals > 0 else 0

            st.markdown("### 🚦 Risk/Ödül Kartı")
            rr_color = "#10b981" if rr_ratio >= 2 else ("#f59e42" if rr_ratio >= 1 else "#ef4444")
            st.markdown(
                f"<div style='background:{rr_color};color:#fff;padding:16px;border-radius:12px;font-size:1.3em;font-weight:bold;'>R/R Oranı: {rr_ratio:.2f} | Maksimum Kayıp: {max_drawdown:.2f} | Kelly: {kelly:.2f}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("### 📈 Getiri & Hedefleme")
            st.markdown(f"Hedef Getiri: %{take_profit_mean:.2f} | CAGR: %{cagr:.2f}")

            st.markdown("### 🤖 Strateji & Uyum")
            st.markdown(f"Başarı Oranı (Win Rate): %{win_rate:.1f} | Ortalama Skor: {avg_score:.2f}")

            st.dataframe(filtered, use_container_width=True)

            # Simülasyon ve Pozisyon Girişi
            st.markdown("---")
            st.markdown("### 🔬 Simülasyon & Pozisyon Girişi")
            st.button("Geriye Dönük Testi Çalıştır", key="backtest_run")
            st.button("Pozisyonu Ayarla / Emri Gönder", key="order_run")
            
        except Exception as e:
            st.error(f"Geçmiş sinyaller yüklenirken hata oluştu: {e}")
    else:
        st.info("Henüz geçmiş sinyal kaydı bulunmamaktadır.")
