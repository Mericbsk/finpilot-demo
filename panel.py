import hashlib
from pathlib import Path
from typing import List, Optional

import streamlit as st
import pandas as pd
import yfinance as yf

from altdata import get_altdata_history
from drl.analysis import RegimeStats, build_narrative_payload, summarize_alternative_signals
from scanner import evaluate_symbol, load_symbols


WORKSPACE_ROOT = Path(__file__).resolve().parent
SHORTLIST_PATTERN = "shortlist_*.csv"
DEMO_SYMBOLS = ["AAPL", "MSFT", "NVDA", "ETH-USD", "BTC-USD"]


def _list_all_shortlists(directory: Path) -> List[Path]:
    return sorted(directory.glob(SHORTLIST_PATTERN))


def _find_latest_shortlist(directory: Path) -> Optional[Path]:
    candidates = _list_all_shortlists(directory)
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _extract_symbols_from_frame(frame: pd.DataFrame) -> List[str]:
    candidate_columns = ["Symbol", "symbol", "Ticker", "ticker"]
    for column in candidate_columns:
        if column in frame.columns:
            series = frame[column].dropna().astype(str).str.strip()
            clean = [value for value in series if value]
            unique_symbols = sorted(dict.fromkeys(clean))
            if unique_symbols:
                return unique_symbols
    raise KeyError("CSV dosyasında 'Symbol' veya 'Ticker' başlıklı bir sütun bulunamadı.")


def _hash_uploaded_file(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    data = uploaded_file.getvalue()
    return hashlib.sha1(data).hexdigest()


def _set_active_symbols(symbols: List[str], *, source: str, status: str) -> None:
    st.session_state.active_symbols = symbols
    st.session_state.symbol_source = source
    st.session_state.data_status = {
        "type": "success",
        "message": status,
        "count": len(symbols),
        "source": source,
    }
    st.session_state.pending_scroll = True


MODES = (
    {"label": "📊 Analiz Paneli", "key": "Analiz Paneli"},
    {"label": "⚙️ Kişiselleştirme", "key": "Kişiselleştirme"},
)


def _mode_labels():
    return [mode["label"] for mode in MODES]


def _mode_from_label(label: str) -> str:
    for mode in MODES:
        if mode["label"] == label:
            return mode["key"]
    return MODES[0]["key"]


def _icon_for_strength(strength: str) -> str:
    mapping = {
        "positive_strong": "🟢",
        "positive_moderate": "🟢",
        "positive_light": "🟢",
        "positive_neutral": "🟡",
        "neutral": "🟡",
        "negative_light": "🟠",
        "negative_moderate": "🟠",
        "negative_strong": "🔴",
    }
    return mapping.get(strength, "🔘")


def _regime_name(raw_value) -> str:
    if isinstance(raw_value, str):
        return raw_value
    if isinstance(raw_value, bool):
        return "trend" if raw_value else "range"
    if raw_value is None:
        return "bilinmiyor"
    return str(raw_value)


if "dashboard_mode" not in st.session_state:
    st.session_state.dashboard_mode = MODES[0]["key"]

if "personalization" not in st.session_state:
    st.session_state.personalization = {
        "risk_profile": "Dengeli",
        "strategy_focus": ["Trend Takibi"],
        "notifications": {"email": True, "telegram": False},
        "notes": "",
    }

if "portfolio_value" not in st.session_state:
    st.session_state.portfolio_value = 10_000

if "risk_percent" not in st.session_state:
    st.session_state.risk_percent = 2.0

if "active_symbols" not in st.session_state:
    st.session_state.active_symbols = load_symbols()

if "symbol_source" not in st.session_state:
    st.session_state.symbol_source = "demo"

if "data_status" not in st.session_state:
    st.session_state.data_status = None

if "pending_scroll" not in st.session_state:
    st.session_state.pending_scroll = False

if "last_csv_hash" not in st.session_state:
    st.session_state.last_csv_hash = None

st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] {
        border-radius: 10px;
        padding: 0.55rem 0.75rem 0.55rem 0.85rem;
        margin-bottom: 0.45rem;
        border: 1px solid transparent;
        background: #f8fafc;
        transition: all 0.2s ease-in-out;
        position: relative;
        font-weight: 500;
        color: #475569;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background: #eef2ff;
        color: #1d4ed8;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]::before {
        content: "";
        position: absolute;
        left: 0;
        top: 12%;
        bottom: 12%;
        width: 4px;
        border-radius: 2px;
        background: transparent;
        transition: background 0.2s ease-in-out;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {
        background: #e0ecff;
        border-color: #2563eb;
        color: #1e3a8a;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"]::before {
        background: #2563eb;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] p {
        margin: 0;
    }
    div.data-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.1rem;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    div.data-card h3 {
        margin: 0;
        font-size: 1.1rem;
        color: #0f172a;
    }
    div.data-card p.option-desc {
        color: #475569;
        margin: 0;
        font-size: 0.95rem;
    }
    div.data-card .status-tag {
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.55rem;
        border-radius: 999px;
    }
    div.data-card .status-tag.success {
        background: rgba(34, 197, 94, 0.12);
        color: #166534;
    }
    div.data-card .status-tag.warning {
        background: rgba(251, 191, 36, 0.15);
        color: #92400e;
    }
    div.data-card .status-tag.error {
        background: rgba(239, 68, 68, 0.15);
        color: #b91c1c;
    }
    div.data-card button[data-testid="baseButton-secondary"]{
        width: fit-content;
    }
    div.data-card .small-link {
        font-size: 0.85rem;
        color: #2563eb;
        text-decoration: underline;
        cursor: pointer;
    }
    div.breadcrumb-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #eef2ff;
        border-left: 4px solid #2563eb;
        padding: 0.45rem 0.85rem;
        border-radius: 12px;
        font-weight: 600;
        color: #1d4ed8;
        margin: 0.5rem 0 1.0rem 0;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar - Navigasyon ve Ayarlar
with st.sidebar:
    st.markdown("## ⚙️ Kontrol Merkezi")
    st.markdown("### 🔀 Sayfa Seç")
    mode_labels = _mode_labels()
    current_label = next(
        (mode_cfg["label"] for mode_cfg in MODES if mode_cfg["key"] == st.session_state.dashboard_mode),
        mode_labels[0],
    )
    selected_label = st.radio(
        "Sayfa Seç",
        mode_labels,
        key="dashboard_mode_label",
        index=mode_labels.index(current_label),
    )
    st.session_state.dashboard_mode = _mode_from_label(selected_label)

    st.markdown("---")
    st.markdown("### 💼 Portföy & Risk")
    portfolio_value_input = st.number_input(
        "Portföy Değeri ($)",
        value=int(st.session_state.portfolio_value),
        step=1000,
        min_value=1000,
    )
    risk_percent_input = st.slider(
        "Risk Yüzdesi (%)",
        min_value=1.0,
        max_value=5.0,
        value=float(st.session_state.risk_percent),
        step=0.5,
    )

    st.session_state.portfolio_value = float(portfolio_value_input)
    st.session_state.risk_percent = float(risk_percent_input)

    st.markdown("### 🎯 Sistem Kriterleri")
    st.markdown(
        """
        **📊 Ana Filtreler:**
        - 🟢 Uzun vadeli trend (200 EMA üstü)
        - 🟡 Orta vadeli trend (50 EMA üstü) 
        - 🔴 Kısa vadeli sinyaller (2+ sinyal)

        **✨ Ek Güçlü Filtreler:**
        - 📈 Hacim artışı (1.5x normalin üstü)
        - 🚀 Fiyat momentum (3 günde %2+)
        - 💪 Trend gücü (EMA farkı %3+)

        **🛡️ Risk Yönetimi:**
        - Stop-loss: ATR x 2
        - Take-profit: Risk x 2
        - Maksimum risk: Portföy %2'si
        """
    )

portfolio_value = float(st.session_state.portfolio_value)
risk_percent = float(st.session_state.risk_percent)
mode = st.session_state.dashboard_mode
mode_icon = next((mode_cfg["label"].split()[0] for mode_cfg in MODES if mode_cfg["key"] == mode), "📊")
mode_label_text = next((mode_cfg["label"].split(" ", 1)[1] for mode_cfg in MODES if mode_cfg["key"] == mode), mode)

if mode == "Kişiselleştirme":
    st.markdown("# ⚙️ Şu an: Kişiselleştirme")
    st.write("Ayarlarınızı güncelledikten sonra sinyal tablolarını yenileyin.")
    st.info("Kaydet tuşu portföy ve risk parametrelerini günceller ve sizi ana panele yönlendirir.")

    personalization_state = st.session_state.personalization
    strategy_options = ["Trend Takibi", "Ortalama Dönüş", "Volatilite Boşlukları", "Momentum"]

    with st.form("personalization_form"):
        st.subheader("Risk Profili")
        risk_profile = st.select_slider(
            "Profil",
            options=["Defansif", "Dengeli", "Agresif"],
            value=personalization_state.get("risk_profile", "Dengeli"),
        )

        st.subheader("Strateji Tercihleri")
        strategy_focus = st.multiselect(
            "Odaklanmak istediğiniz stratejiler",
            strategy_options,
            default=[s for s in personalization_state.get("strategy_focus", []) if s in strategy_options] or ["Trend Takibi"],
        )

        st.subheader("Bildirimler")
        notify_email = st.checkbox(
            "Email bildirimleri",
            value=personalization_state.get("notifications", {}).get("email", True),
        )
        notify_telegram = st.checkbox(
            "Telegram sinyal pingleri",
            value=personalization_state.get("notifications", {}).get("telegram", False),
        )

        st.subheader("Portföy Parametreleri")
        custom_portfolio_value = st.number_input(
            "Portföy Değeri ($)",
            value=int(portfolio_value),
            step=1000,
            min_value=1000,
        )
        custom_risk_percent = st.slider(
            "Maksimum risk (%)",
            min_value=1.0,
            max_value=5.0,
            value=float(risk_percent),
            step=0.5,
        )

        st.subheader("Notlar")
        notes = st.text_area(
            "Kısa notlarınızı girin",
            value=personalization_state.get("notes", ""),
            placeholder="Örn. Makro risk yüksek olduğunda kaldıraç kullanma",
        )

        submitted = st.form_submit_button("Kaydet ve Analize Dön")

    back_clicked = st.button("Kaydetmeden Ana Ekrana Dön")

    if submitted:
        st.session_state.personalization = {
            "risk_profile": risk_profile,
            "strategy_focus": strategy_focus,
            "notifications": {"email": notify_email, "telegram": notify_telegram},
            "notes": notes,
        }

        st.session_state.portfolio_value = float(custom_portfolio_value)
        st.session_state.risk_percent = float(custom_risk_percent)

        st.session_state.dashboard_mode = MODES[0]
        st.experimental_rerun()  # type: ignore[attr-defined]

    if back_clicked:
        st.session_state.dashboard_mode = MODES[0]
        st.experimental_rerun()  # type: ignore[attr-defined]

    st.stop()

# Header
st.markdown("# 📈 Trading Dashboard + Risk Yönetimi")
st.markdown(
    f"<div class='breadcrumb-badge'>{mode_icon} Şu an: {mode_label_text}</div>",
    unsafe_allow_html=True,
)

active_personalization = st.session_state.personalization
selected_strategies = ", ".join(active_personalization.get("strategy_focus", [])) or "Trend Takibi"
st.caption(
    f"Aktif profil: {active_personalization.get('risk_profile', 'Dengeli')} • Strateji odağı: {selected_strategies}."
    " Ayarları güncellemek için sol menüden **Kişiselleştirme** sekmesini açın."
)

if st.button("⚙️ Kişiselleştirmeyi Aç"):
    st.session_state.dashboard_mode = MODES[1]
    st.experimental_rerun()  # type: ignore[attr-defined]

st.markdown("## 📥 Analiz Veri Kaynağınızı Seçin")
st.markdown(
    "Lütfen analiz edilecek sembol setini belirleyin. Mevcut shortlist'i hızlıca yükleyebilir, kendi CSV dosyanızı tanımlayabilir veya platformu keşfetmek için demo verisini kullanabilirsiniz."
)

latest_shortlist_path = _find_latest_shortlist(WORKSPACE_ROOT)
latest_shortlist_symbols: List[str] = []
latest_shortlist_count: Optional[int] = None
shortlist_load_error: Optional[str] = None

if latest_shortlist_path:
    try:
        shortlist_frame = pd.read_csv(latest_shortlist_path)
        latest_shortlist_symbols = _extract_symbols_from_frame(shortlist_frame)
        latest_shortlist_count = len(latest_shortlist_symbols)
    except Exception as exc:
        shortlist_load_error = str(exc)
else:
    shortlist_load_error = "Kayıtlı shortlist bulunamadı."

sample_template = pd.DataFrame({"Symbol": ["AAPL", "MSFT", "NVDA"]})

card_cols = st.columns(3)

with card_cols[0]:
    st.markdown("<div class='data-card'>", unsafe_allow_html=True)
    st.markdown("### 🗂 Son Shortlist’i Yükle", unsafe_allow_html=True)
    st.markdown(
        "<p class='option-desc'>En son kaydettiğiniz tarama sonuçlarını tekrar inceleyin.</p>",
        unsafe_allow_html=True,
    )

    shortlist_label = "Shortlist’i Yükle"
    if latest_shortlist_count:
        shortlist_label = f"Shortlist’i Yükle ({latest_shortlist_count} sembol)"

    shortlist_button = st.button(shortlist_label, key="load_latest_shortlist")

    if shortlist_button:
        if latest_shortlist_symbols:
            _set_active_symbols(
                latest_shortlist_symbols,
                source="shortlist",
                status=f"📂 Son shortlist başarıyla yüklendi ({len(latest_shortlist_symbols)} sembol)",
            )
            st.session_state.last_csv_hash = None
            st.experimental_rerun()  # type: ignore[attr-defined]
        else:
            st.session_state.data_status = {
                "type": "warning",
                "message": "📁 Yüklenecek shortlist bulunamadı veya okunamadı.",
                "source": "shortlist",
            }
            st.session_state.pending_scroll = False
            st.experimental_rerun()  # type: ignore[attr-defined]

    if st.session_state.data_status and st.session_state.data_status.get("source") == "shortlist":
        tag_type = st.session_state.data_status.get("type", "success")
        message = st.session_state.data_status.get("message", "")
        st.markdown(
            f"<span class='status-tag {tag_type}' role='status'>{message}</span>",
            unsafe_allow_html=True,
        )
    elif shortlist_load_error and not latest_shortlist_symbols:
        st.markdown(
            f"<span class='status-tag warning' role='status'>⚠️ {shortlist_load_error}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with card_cols[1]:
    st.markdown("<div class='data-card'>", unsafe_allow_html=True)
    st.markdown("### 📄 CSV Yükle", unsafe_allow_html=True)
    st.markdown(
        "<p class='option-desc'>Kendi sembol listenizi yükleyin (Symbol/Ticker sütunu içermeli).</p>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Dosyanızı buraya sürükleyin veya seçin",
        type=["csv"],
        accept_multiple_files=False,
        key="custom_csv_upload",
        help="Yalnızca .csv formatı desteklenir.",
    )

    st.download_button(
        label="Örnek Şablonu İndir",
        data=sample_template.to_csv(index=False).encode("utf-8"),
        file_name="finpilot_ornek_symbol_listesi.csv",
        mime="text/csv",
        key="sample_csv_download",
    )

    if uploaded_file is not None:
        file_hash = _hash_uploaded_file(uploaded_file)
        if file_hash != st.session_state.last_csv_hash:
            try:
                csv_frame = pd.read_csv(uploaded_file)
                symbols = _extract_symbols_from_frame(csv_frame)
                if not symbols:
                    raise ValueError("En az bir sembol içermeli.")
                _set_active_symbols(
                    symbols,
                    source="csv",
                    status=f"✅ CSV başarıyla yüklendi ({len(symbols)} sembol)",
                )
                st.session_state.last_csv_hash = file_hash
                st.experimental_rerun()  # type: ignore[attr-defined]
            except KeyError as exc:
                st.session_state.data_status = {
                    "type": "error",
                    "message": f"❌ Hata: {exc}",
                    "source": "csv",
                }
                st.session_state.pending_scroll = False
                st.experimental_rerun()  # type: ignore[attr-defined]
            except Exception as exc:
                st.session_state.data_status = {
                    "type": "error",
                    "message": f"❌ Hata: {exc}",
                    "source": "csv",
                }
                st.session_state.pending_scroll = False
                st.experimental_rerun()  # type: ignore[attr-defined]

    if st.session_state.data_status and st.session_state.data_status.get("source") == "csv":
        tag_type = st.session_state.data_status.get("type", "success")
        message = st.session_state.data_status.get("message", "")
        st.markdown(
            f"<span class='status-tag {tag_type}' role='status'>{message}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with card_cols[2]:
    st.markdown("<div class='data-card'>", unsafe_allow_html=True)
    st.markdown("### 🎯 Demo Verisi Kullan", unsafe_allow_html=True)
    st.markdown(
        "<p class='option-desc'>Gerçek veriniz yoksa örnek bir analiz çalıştırabilirsiniz.</p>",
        unsafe_allow_html=True,
    )

    demo_button = st.button("Demo Verisi ile Çalıştır (5 sembol)", key="use_demo_symbols")
    if demo_button:
        _set_active_symbols(
            DEMO_SYMBOLS,
            source="demo",
            status="🟢 Demo modu aktif (5 sembol)",
        )
        st.session_state.last_csv_hash = None
        st.experimental_rerun()  # type: ignore[attr-defined]

    if st.session_state.data_status and st.session_state.data_status.get("source") == "demo":
        tag_type = st.session_state.data_status.get("type", "success")
        message = st.session_state.data_status.get("message", "")
        st.markdown(
            f"<span class='status-tag {tag_type}' role='status'>{message}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

if st.session_state.pending_scroll:
    st.markdown(
        """
        <script>
        const target = document.getElementById('analysis-results');
        if (target) {
            target.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.pending_scroll = False

source_labels = {
    "shortlist": "Son Shortlist",
    "csv": "Özel CSV",
    "demo": "Demo Verisi",
}
active_source = st.session_state.get("symbol_source", "demo")
active_count = len(st.session_state.get("active_symbols", []))
st.info(
    f"📌 Aktif kaynak: {source_labels.get(active_source, 'Varsayılan Liste')} • {active_count} sembol",
    icon="ℹ️",
)

# Ana içerik
overall_success_rate = None
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("<h2 id='analysis-results'>📊 Analiz Sonuçları</h2>", unsafe_allow_html=True)
    
    # Veri toplama
    with st.spinner("Semboller analiz ediliyor..."):
        symbols = st.session_state.get("active_symbols") or load_symbols()
        results = []
        df = pd.DataFrame()  # Initialize df
        for sym in symbols:
            info = evaluate_symbol(sym)
            if info:
                results.append(info)

    if not results:
        st.error("❌ Hiçbir sembol kriterleri karşılamıyor.")
        st.info("💡 Bu normal - kriterlerimiz sıkı. Sabırla bekleyin!")
    else:
        df = pd.DataFrame(results)
        df = df.sort_values(["entry_ok", "score"], ascending=[False, False])
        if not df.empty:
            overall_success_rate = float(df["entry_ok"].astype(float).mean())

        # Alım fırsatları
        buyable = df[df["entry_ok"]]
        if len(buyable) > 0:
            st.success(f"🟢 **{len(buyable)} ALIM FIRSATI!**")

            # Sade tablo
            display_cols = ["symbol", "price", "stop_loss", "take_profit", "position_size", "risk_reward"]
            buyable_display = buyable[display_cols].copy()
            buyable_display.columns = ["Sembol", "Fiyat", "Stop-Loss", "Take-Profit", "Lot", "R/R"]

            st.dataframe(buyable_display, width='stretch')

        # Tüm sonuçlar (sade)
        st.markdown("### 📋 Tüm Semboller")
        simple_cols = ["symbol", "price", "score", "entry_ok", "risk_reward"]
        df_simple = df[simple_cols].copy()
        df_simple.columns = ["Sembol", "Fiyat", "Skor", "Alım?", "R/R"]
        st.dataframe(df_simple, width='stretch')

with col2:
    st.markdown("## 🔍 Detay Analiz")
    
    if 'df' in locals() and len(df) > 0:
        selected = st.selectbox("Sembol Seç:", df["symbol"].tolist())
        
        if selected:
            row = df[df["symbol"] == selected].iloc[0]
            history = get_altdata_history(selected, periods=36, freq="H")
            sentiment_signal, whale_signal = summarize_alternative_signals(history)

            price = float(row["price"])
            stop_loss = float(row["stop_loss"])
            take_profit = float(row["take_profit"])
            position_size = float(row["position_size"])
            risk_reward = float(row["risk_reward"])

            drawdown_fraction = None
            if price > 0:
                drawdown_fraction = max(0.0, min(1.0, (price - stop_loss) / price))

            regime_stats = RegimeStats(
                name=_regime_name(row.get("regime")),
                success_rate=overall_success_rate,
                average_reward=risk_reward if risk_reward > 0 else None,
                max_drawdown=drawdown_fraction,
            )
            narrative = build_narrative_payload(
                regime_stats,
                sentiment_signal,
                whale_signal,
                current_price=price,
                max_allowed_drawdown=risk_percent / 100.0,
            )
            
            # Alım Önerisi - Sade
            if row['entry_ok']:
                st.success("🟢 ALIM ÖNERİSİ")
            else:
                st.warning("🟡 BEKLEYİN")
            
            # Risk Bilgileri - Sade ve Net
            st.markdown("### 🛡️ Risk Planı")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Giriş", f"${price}")
                st.metric("Stop-Loss", f"${stop_loss}")
            with col_b:
                st.metric("Hedef", f"${take_profit}")
                st.metric("Lot", f"{position_size}")

            st.markdown("### 🧠 Alternatif Veri Özeti")
            for signal in (sentiment_signal, whale_signal):
                icon = _icon_for_strength(signal.strength)
                st.markdown(f"{icon} **{signal.name}:** {signal.description}")

            st.markdown("### 🗣️ Kişiselleştirilmiş Yorum")
            st.markdown(f"**{narrative.title_1}** {narrative.text_1}")
            st.markdown(f"**{narrative.title_2}** {narrative.text_2}")
            exit_price = narrative.exit_price
            if exit_price:
                st.info(f"🔻 Stop seviyesi önerisi: ${exit_price:,.2f}")
            st.caption(
                f"{active_personalization.get('risk_profile', 'Dengeli')} profiliniz ve portföy %{risk_percent:.1f} riski birlikte değerlendirildi."
            )

            # ✨ Yeni Filtre Durumları 
            st.markdown("### ✨ Filtre Kontrol")
            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                icon = "🟢" if row.get('volume_spike', False) else "🔴"
                st.write(f"{icon} Hacim")
            with filter_col2:
                icon = "🟢" if row.get('price_momentum', False) else "🔴"
                st.write(f"{icon} Momentum")
            with filter_col3:
                icon = "🟢" if row.get('trend_strength', False) else "🔴"
                st.write(f"{icon} Trend Gücü")

            st.info(f"📊 Filtre Skoru: {row.get('filter_score', 0)}/3")

            # Risk/Reward görsel
            if risk_reward >= 2:
                st.success(f"✅ R/R: {risk_reward:.1f} (İYİ)")
            else:
                st.error(f"❌ R/R: {risk_reward:.1f} (KÖTÜ)")

            # Basit hesaplama gösterimi
            risk_amount = price - stop_loss
            reward_amount = take_profit - price
            total_risk = risk_amount * position_size
            total_reward = reward_amount * position_size
            
            st.markdown(f"""
            **💰 Para Hesabı:**
            - Maksimum Kayıp: ${total_risk:.0f}
            - Potansiyel Kazanç: ${total_reward:.0f}
            - Risk Yüzdesi: {(total_risk/portfolio_value)*100:.1f}%
            """)
            
            # Grafik - Basit
            st.markdown("### 📊 Fiyat Grafiği")
            try:
                df_chart = yf.download(selected, interval="1d", period="30d", progress=False)
                if df_chart is not None and not df_chart.empty:
                    st.line_chart(df_chart['Close'])
            except Exception:
                st.warning("Grafik yüklenemedi")

# Footer
st.markdown("---")
st.markdown("🔥 **Basit Strateji:** Yeşil olanları al, stop ve hedefle bekle!")
