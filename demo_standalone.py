"""
FinPilot Demo - Standalone Public Version
==========================================

Sadece demo sayfasını içeren, internete yüklenmeye hazır versiyon.
Waitlist/email toplama özelliği ile.

Kullanım:
    streamlit run demo_standalone.py
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="FinPilot - AI Trading Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://finpilot.ai/help",
        "Report a bug": "https://finpilot.ai/feedback",
        "About": "# FinPilot AI Trading Platform\nAI-powered stock analysis for smart investors.",
    },
)

# Custom CSS for better branding
st.markdown(
    """
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom colors */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* Signup banner */
    .signup-banner {
        background: linear-gradient(90deg, #00e6e6 0%, #0ea5e9 100%);
        padding: 15px 25px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .signup-banner h3 {
        color: #0f172a;
        margin: 0;
    }

    .signup-banner p {
        color: #1e293b;
        margin: 0;
    }

    /* Waitlist form */
    .waitlist-card {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid #334155;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
    }

    /* Feature badges */
    .demo-badge {
        background: #fbbf24;
        color: #0f172a;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }

    .pro-badge {
        background: #00e6e6;
        color: #0f172a;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Waitlist data storage
WAITLIST_FILE = "data/waitlist.json"


def save_to_waitlist(email: str, name: str = "", source: str = "demo") -> bool:
    """Save email to waitlist."""
    try:
        Path("data").mkdir(exist_ok=True)

        # Load existing
        waitlist = []
        if Path(WAITLIST_FILE).exists():
            with open(WAITLIST_FILE, "r") as f:
                waitlist = json.load(f)

        # Check if already exists
        if any(w["email"].lower() == email.lower() for w in waitlist):
            return False  # Already registered

        # Add new entry
        waitlist.append(
            {
                "email": email.lower(),
                "name": name,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "ip": "anonymous",  # Privacy first
            }
        )

        # Save
        with open(WAITLIST_FILE, "w") as f:
            json.dump(waitlist, f, indent=2)

        return True
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")
        return False


def render_signup_banner():
    """Render the signup/waitlist banner at top."""
    st.markdown(
        """
    <div class="signup-banner">
        <div>
            <h3>🚀 FinPilot Pro'yu Deneyin!</h3>
            <p>1000+ hisse, gerçek zamanlı veri, kişisel portföy takibi</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_waitlist_sidebar():
    """Render waitlist signup form in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📧 Erken Erişim")
        st.caption("Pro versiyonu ilk deneyenlerden olun!")

        with st.form("waitlist_form", clear_on_submit=True):
            email = st.text_input("E-posta", placeholder="ornek@email.com")
            name = st.text_input("İsim (opsiyonel)", placeholder="Adınız")

            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("🎯 Katıl", use_container_width=True)

            if submitted:
                if not email or "@" not in email:
                    st.error("Geçerli e-posta girin")
                else:
                    success = save_to_waitlist(email, name)
                    if success:
                        st.success("✅ Listeye eklendi!")
                        st.balloons()
                    else:
                        st.info("📧 Zaten kayıtlısınız!")

        # Show waitlist count
        try:
            if Path(WAITLIST_FILE).exists():
                with open(WAITLIST_FILE, "r") as f:
                    count = len(json.load(f))
                if count > 0:
                    st.caption(f"👥 {count} kişi bekliyor")
        except:
            pass


def render_feature_comparison():
    """Show Demo vs Pro features."""
    st.markdown("### 🎯 Demo vs Pro")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        <div class="waitlist-card">
            <span class="demo-badge">DEMO</span>
            <h4 style="color: #f8fafc; margin-top: 15px;">Ücretsiz Demo</h4>
            <ul style="color: #cbd5f5;">
                <li>✅ 10 popüler hisse</li>
                <li>✅ Temel AI analizi</li>
                <li>✅ Teknik indikatörler</li>
                <li>❌ Gerçek zamanlı veri</li>
                <li>❌ Portföy takibi</li>
                <li>❌ Kişisel tarama</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="waitlist-card" style="border-color: #00e6e6;">
            <span class="pro-badge">PRO</span>
            <h4 style="color: #00e6e6; margin-top: 15px;">FinPilot Pro</h4>
            <ul style="color: #cbd5f5;">
                <li>✅ 1000+ hisse (BIST & NASDAQ)</li>
                <li>✅ Gelişmiş AI + DRL modelleri</li>
                <li>✅ Gerçek zamanlı veri</li>
                <li>✅ Kişisel portföy takibi</li>
                <li>✅ Özel tarama filtreleri</li>
                <li>✅ Telegram bildirimleri</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_cta_section():
    """Render call-to-action with email signup."""
    st.markdown("---")

    st.markdown(
        """
    <div style='background: linear-gradient(90deg, rgba(0,230,230,0.1) 0%, rgba(14,165,233,0.1) 100%);
                padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #00e6e6;'>
        <h2 style='color: #f8fafc;'>🚀 Pro Versiyona Hazır mısınız?</h2>
        <p style='color: #cbd5f5; font-size: 1.1em; max-width: 600px; margin: 0 auto 20px auto;'>
            Erken erişim listesine katılın, lansmanda <strong style="color: #00e6e6;">%50 indirim</strong> kazanın!
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Centered email form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("cta_waitlist", clear_on_submit=True):
            email = st.text_input(
                "E-posta adresiniz", placeholder="ornek@email.com", label_visibility="collapsed"
            )

            if st.form_submit_button(
                "🎯 Erken Erişim Listesine Katıl", use_container_width=True, type="primary"
            ):
                if email and "@" in email:
                    success = save_to_waitlist(email, source="cta")
                    if success:
                        st.success("🎉 Harika! Listeye eklendiniz. Lansmanı kaçırmayacaksınız!")
                        st.balloons()
                    else:
                        st.info("👋 Zaten listemizdesiniz!")
                else:
                    st.error("Geçerli bir e-posta adresi girin")


def main():
    """Main demo application."""

    # Signup banner at top
    render_signup_banner()

    # Waitlist form in sidebar
    render_waitlist_sidebar()

    # Language selector in sidebar
    with st.sidebar:
        st.markdown("### 🌐 Language")
        lang = st.selectbox(
            "Dil Seçin", ["English", "Türkçe", "Deutsch"], index=1, label_visibility="collapsed"
        )
        lang_map = {"English": "en", "Türkçe": "tr", "Deutsch": "de"}
        st.session_state.language = lang_map[lang]

    # Import and render demo page
    try:
        from views.demo import render_demo_page

        render_demo_page()
    except Exception as e:
        st.error(f"Demo yüklenirken hata: {e}")
        st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")

    # Feature comparison
    render_feature_comparison()

    # CTA section
    render_cta_section()

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #64748b; padding: 20px;'>
        <p>© 2026 FinPilot. Tüm hakları saklıdır.</p>
        <p style='font-size: 12px;'>
            ⚠️ Yatırım tavsiyesi değildir. Finansal kararlarınızdan kendiniz sorumlusunuz.
        </p>
        <p style='font-size: 12px;'>
            <a href="#" style="color: #00e6e6;">Gizlilik Politikası</a> |
            <a href="#" style="color: #00e6e6;">Kullanım Şartları</a> |
            <a href="#" style="color: #00e6e6;">İletişim</a>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
