"""
FinPilot Demo - Standalone Public Version
==========================================

Public demo with:
- 30 categories, 100+ unique stocks
- Multi-language support (EN/DE/TR) - English default
- Waitlist/email collection
- Feature comparison

Usage:
    streamlit run demo_standalone.py
"""

import json
from datetime import datetime
from pathlib import Path

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

# ============================================
# 🌐 TRANSLATIONS
# ============================================

UI_TRANSLATIONS = {
    "en": {
        "hero_title": "FinPilot Global Demo",
        "hero_subtitle": "AI-Powered Analysis for NASDAQ & S&P 500 Giants",
        "hero_cta": "Analyze Like a Pro — Start for Free",
        "try_pro": "🚀 Try FinPilot Pro!",
        "pro_features": "1000+ stocks, real-time data, personal portfolio tracking",
        "language": "🌐 Language",
        "early_access": "📧 Early Access",
        "early_access_desc": "Be among the first to try Pro!",
        "email": "Email",
        "email_placeholder": "example@email.com",
        "name": "Name (optional)",
        "name_placeholder": "Your name",
        "join": "🎯 Join",
        "join_error": "Enter a valid email",
        "join_success": "✅ Added to list!",
        "join_already": "📧 Already registered!",
        "waiting_count": "👥 {count} people waiting",
        "demo_vs_pro": "🎯 Demo vs Pro",
        "free_demo": "Free Demo",
        "finpilot_pro": "FinPilot Pro",
        "demo_features": [
            "✅ 100+ popular stocks",
            "✅ Basic AI analysis",
            "✅ Technical indicators",
            "❌ Real-time data",
            "❌ Portfolio tracking",
            "❌ Custom scanning",
        ],
        "pro_features_list": [
            "✅ 1000+ stocks (BIST & NASDAQ)",
            "✅ Advanced AI + DRL models",
            "✅ Real-time data",
            "✅ Personal portfolio tracking",
            "✅ Custom scan filters",
            "✅ Telegram notifications",
        ],
        "ready_for_pro": "🚀 Ready for Pro Version?",
        "cta_desc": "Join the early access list, get <strong style='color: #00e6e6;'>50% discount</strong> at launch!",
        "join_early_access": "🎯 Join Early Access List",
        "cta_success": "🎉 Great! You're on the list!",
        "cta_already": "👋 You're already on our list!",
        "cta_error": "Enter a valid email address",
        "copyright": "© 2026 FinPilot. All rights reserved.",
        "disclaimer": "⚠️ Not investment advice. You are responsible for your own financial decisions.",
        "privacy": "Privacy Policy",
        "terms": "Terms of Service",
        "contact": "Contact",
        "demo_error": "Error loading demo: {error}",
        "demo_retry": "Please refresh the page or try again later.",
        "stock_categories": "📊 Stock Categories",
        "categories_desc": "Choose a category to analyze stocks",
        "stocks": "stocks",
        "selected_category": "✅ **{name}** selected ({count} stocks)",
        "analyze": "📈 Analyze",
        "quick_picks": "⚡ Quick Picks",
    },
    "de": {
        "hero_title": "FinPilot Global Demo",
        "hero_subtitle": "KI-gestützte Analyse für NASDAQ & S&P 500 Giganten",
        "hero_cta": "Analysieren wie ein Profi — Kostenlos starten",
        "try_pro": "🚀 FinPilot Pro testen!",
        "pro_features": "1000+ Aktien, Echtzeitdaten, Portfolio-Verfolgung",
        "language": "🌐 Sprache",
        "early_access": "📧 Früher Zugang",
        "early_access_desc": "Gehören Sie zu den Ersten!",
        "email": "E-Mail",
        "email_placeholder": "beispiel@email.com",
        "name": "Name (optional)",
        "name_placeholder": "Ihr Name",
        "join": "🎯 Beitreten",
        "join_error": "Gültige E-Mail eingeben",
        "join_success": "✅ Zur Liste hinzugefügt!",
        "join_already": "📧 Bereits registriert!",
        "waiting_count": "👥 {count} Personen warten",
        "demo_vs_pro": "🎯 Demo vs Pro",
        "free_demo": "Kostenlose Demo",
        "finpilot_pro": "FinPilot Pro",
        "demo_features": [
            "✅ 100+ Aktien",
            "✅ KI-Analyse",
            "✅ Technische Indikatoren",
            "❌ Echtzeitdaten",
            "❌ Portfolio",
            "❌ Scannen",
        ],
        "pro_features_list": [
            "✅ 1000+ Aktien",
            "✅ Erweiterte KI + DRL",
            "✅ Echtzeitdaten",
            "✅ Portfolio-Verfolgung",
            "✅ Scanfilter",
            "✅ Telegram",
        ],
        "ready_for_pro": "🚀 Bereit für Pro?",
        "cta_desc": "Early Access Liste beitreten, <strong style='color: #00e6e6;'>50% Rabatt</strong>!",
        "join_early_access": "🎯 Early Access beitreten",
        "cta_success": "🎉 Großartig! Sie sind auf der Liste!",
        "cta_already": "👋 Sie sind bereits registriert!",
        "cta_error": "Gültige E-Mail eingeben",
        "copyright": "© 2026 FinPilot. Alle Rechte vorbehalten.",
        "disclaimer": "⚠️ Keine Anlageberatung.",
        "privacy": "Datenschutz",
        "terms": "Nutzungsbedingungen",
        "contact": "Kontakt",
        "demo_error": "Fehler: {error}",
        "demo_retry": "Bitte aktualisieren Sie die Seite.",
        "stock_categories": "📊 Aktienkategorien",
        "categories_desc": "Kategorie wählen",
        "stocks": "Aktien",
        "selected_category": "✅ **{name}** ({count} Aktien)",
        "analyze": "📈 Analysieren",
        "quick_picks": "⚡ Schnellauswahl",
    },
    "tr": {
        "hero_title": "FinPilot Global Demo",
        "hero_subtitle": "NASDAQ & S&P 500 Devleri için Yapay Zeka Analizi",
        "hero_cta": "Profesyonel Gibi Analiz Et — Ücretsiz Başla",
        "try_pro": "🚀 FinPilot Pro'yu Deneyin!",
        "pro_features": "1000+ hisse, gerçek zamanlı veri, portföy takibi",
        "language": "🌐 Dil",
        "early_access": "📧 Erken Erişim",
        "early_access_desc": "Pro'yu ilk deneyenlerden olun!",
        "email": "E-posta",
        "email_placeholder": "ornek@email.com",
        "name": "İsim (opsiyonel)",
        "name_placeholder": "Adınız",
        "join": "🎯 Katıl",
        "join_error": "Geçerli e-posta girin",
        "join_success": "✅ Listeye eklendi!",
        "join_already": "📧 Zaten kayıtlısınız!",
        "waiting_count": "👥 {count} kişi bekliyor",
        "demo_vs_pro": "🎯 Demo vs Pro",
        "free_demo": "Ücretsiz Demo",
        "finpilot_pro": "FinPilot Pro",
        "demo_features": [
            "✅ 100+ hisse",
            "✅ AI analizi",
            "✅ Teknik indikatörler",
            "❌ Gerçek zamanlı",
            "❌ Portföy",
            "❌ Tarama",
        ],
        "pro_features_list": [
            "✅ 1000+ hisse",
            "✅ Gelişmiş AI + DRL",
            "✅ Gerçek zamanlı",
            "✅ Portföy takibi",
            "✅ Tarama filtreleri",
            "✅ Telegram",
        ],
        "ready_for_pro": "🚀 Pro'ya Hazır mısınız?",
        "cta_desc": "Erken erişim listesine katılın, <strong style='color: #00e6e6;'>%50 indirim</strong>!",
        "join_early_access": "🎯 Erken Erişime Katıl",
        "cta_success": "🎉 Harika! Listeye eklendiniz!",
        "cta_already": "👋 Zaten listemizdesiniz!",
        "cta_error": "Geçerli e-posta girin",
        "copyright": "© 2026 FinPilot. Tüm hakları saklıdır.",
        "disclaimer": "⚠️ Yatırım tavsiyesi değildir.",
        "privacy": "Gizlilik",
        "terms": "Şartlar",
        "contact": "İletişim",
        "demo_error": "Hata: {error}",
        "demo_retry": "Sayfayı yenileyin.",
        "stock_categories": "📊 Hisse Kategorileri",
        "categories_desc": "Kategori seçin",
        "stocks": "hisse",
        "selected_category": "✅ **{name}** ({count} hisse)",
        "analyze": "📈 Analiz Et",
        "quick_picks": "⚡ Hızlı Seçim",
    },
}


def t(key, **kwargs):
    """Get translated string."""
    lang = st.session_state.get("language", "en")
    text = UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def t_list(key):
    """Get translated list."""
    lang = st.session_state.get("language", "en")
    return UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["en"]).get(key, [])


# ============================================
# 🎨 CUSTOM CSS
# ============================================

st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp {background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);}
    .signup-banner {background: linear-gradient(90deg, #00e6e6 0%, #0ea5e9 100%); padding: 15px 25px; border-radius: 10px; margin-bottom: 20px;}
    .signup-banner h3 {color: #0f172a; margin: 0;}
    .signup-banner p {color: #1e293b; margin: 0;}
    .waitlist-card {background: rgba(30,41,59,0.9); border: 1px solid #334155; border-radius: 15px; padding: 25px; margin: 20px 0;}
    .demo-badge {background: #fbbf24; color: #0f172a; padding: 3px 10px; border-radius: 5px; font-size: 12px; font-weight: bold;}
    .pro-badge {background: #00e6e6; color: #0f172a; padding: 3px 10px; border-radius: 5px; font-size: 12px; font-weight: bold;}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================
# 📁 DATA STORAGE
# ============================================

WAITLIST_FILE = "data/waitlist.json"


def save_to_waitlist(email, name="", source="demo"):
    """Save email to waitlist."""
    try:
        Path("data").mkdir(exist_ok=True)
        waitlist = []
        if Path(WAITLIST_FILE).exists():
            with open(WAITLIST_FILE, "r") as f:
                waitlist = json.load(f)
        if any(w["email"].lower() == email.lower() for w in waitlist):
            return False
        waitlist.append(
            {
                "email": email.lower(),
                "name": name,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "language": st.session_state.get("language", "en"),
            }
        )
        with open(WAITLIST_FILE, "w") as f:
            json.dump(waitlist, f, indent=2)
        return True
    except Exception:
        return False


def get_waitlist_count():
    """Get current waitlist count."""
    try:
        if Path(WAITLIST_FILE).exists():
            with open(WAITLIST_FILE, "r") as f:
                return len(json.load(f))
    except Exception:
        pass
    return 0


# ============================================
# 🎯 UI COMPONENTS
# ============================================


def render_signup_banner():
    st.markdown(
        f"""
    <div style='background: linear-gradient(135deg, rgba(15,23,42,1) 0%, rgba(30,41,59,0.95) 50%, rgba(15,23,42,1) 100%);
                padding: 40px 32px 24px; border-radius: 24px; text-align: center;
                border: 1px solid #334155; margin-bottom: 16px;
                box-shadow: 0 20px 50px -20px rgba(0,230,230,0.08);'>
        <div style='font-size: 3.2em; font-weight: 900; letter-spacing: 0.03em; margin-bottom: 4px;'>
            <span style='color: #00e6e6;'>Fin</span><span style='color: #f8fafc;'>Pilot</span>
        </div>
        <div style='color: #94a3b8; font-size: 1.15em; letter-spacing: 0.5px; margin-bottom: 6px;'>{t("hero_title")}</div>
        <div style='color: #64748b; font-size: 0.95em; letter-spacing: 1px; margin-bottom: 16px;'>{t("hero_subtitle")}</div>
        <div style='width: 60px; height: 2px; background: linear-gradient(90deg, transparent, #00e6e6, transparent); margin: 0 auto 16px auto;'></div>
        <div style='font-size: 0.85em; color: #00e6e6; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 10px; font-weight: 600;'>🚀 {t("hero_cta")}</div>
        <p style='color: #94a3b8; font-size: 0.95em; max-width: 620px; margin: 0 auto 8px auto; line-height: 1.5;'>{t("pro_features")}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Native Streamlit buttons (clickable)
    btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([2, 1.2, 0.3, 1.2, 2])
    with btn_col2:
        if st.button(
            f"🚀 {t('try_pro')}", type="primary", use_container_width=True, key="hero_start"
        ):
            st.session_state.show_waitlist = True
    with btn_col4:
        if st.button(f"🔍 {t('analyze')}", use_container_width=True, key="hero_explore"):
            st.session_state.show_categories = True

    # Badge line
    st.markdown(
        """
    <div style='text-align: center; margin: 4px 0 16px 0; display: flex; justify-content: center; gap: 28px; flex-wrap: wrap;'>
        <span style='color: #475569; font-size: 0.85em;'>⚡ 1000+ Stocks</span>
        <span style='color: #475569; font-size: 0.85em;'>📊 BIST & NASDAQ</span>
        <span style='color: #475569; font-size: 0.85em;'>🤖 AI-Powered</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_language_selector():
    with st.sidebar:
        st.markdown(f"### {t('language')}")
        languages = {"English": "en", "Deutsch": "de", "Türkçe": "tr"}
        current_lang = st.session_state.get("language", "en")
        current_index = (
            list(languages.values()).index(current_lang)
            if current_lang in languages.values()
            else 0
        )
        selected = st.selectbox(
            "Language", list(languages.keys()), index=current_index, label_visibility="collapsed"
        )
        new_lang = languages[selected]
        if new_lang != current_lang:
            st.session_state.language = new_lang
            st.rerun()


def render_waitlist_sidebar():
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### {t('early_access')}")
        st.caption(t("early_access_desc"))
        with st.form("waitlist_form", clear_on_submit=True):
            email = st.text_input(t("email"), placeholder=t("email_placeholder"))
            name = st.text_input(t("name"), placeholder=t("name_placeholder"))
            if st.form_submit_button(t("join"), use_container_width=True):
                if not email or "@" not in email:
                    st.error(t("join_error"))
                else:
                    if save_to_waitlist(email, name):
                        st.success(t("join_success"))
                        st.balloons()
                    else:
                        st.info(t("join_already"))
        count = get_waitlist_count()
        if count > 0:
            st.caption(t("waiting_count", count=count))


def render_category_selector():
    """Render compact stock category selector with quick picks."""
    try:
        from views.components.demo_presets import (
            DEMO_CATEGORIES,
            DEMO_STATS,
            get_categories_by_group,
        )

        lang = st.session_state.get("language", "en")

        # Compact header
        col_title, col_stats = st.columns([2, 1])
        with col_title:
            st.markdown(f"### {t('stock_categories')}")
        with col_stats:
            st.caption(
                f"📊 {DEMO_STATS['total_categories']} categories • {DEMO_STATS['unique_stocks']} stocks"
            )

        # Quick picks - popular categories as horizontal chips
        quick_picks = [
            "magnificent_7",
            "ai_revolution",
            "dividend_kings",
            "clean_energy",
            "fintech_disruptors",
        ]

        st.markdown(
            """
        <style>
        .quick-pick-container { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px; }
        .category-chip {
            background: linear-gradient(135deg, rgba(0,230,230,0.15), rgba(14,165,233,0.1));
            border: 1px solid rgba(0,230,230,0.3); border-radius: 20px; padding: 8px 16px;
            color: #f8fafc; font-size: 0.9em; cursor: pointer; transition: all 0.2s;
        }
        .category-chip:hover { border-color: #00e6e6; background: rgba(0,230,230,0.25); }
        .category-chip.selected { border-color: #00e6e6; background: rgba(0,230,230,0.3); }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Quick picks row
        quick_cols = st.columns(len(quick_picks))
        for idx, key in enumerate(quick_picks):
            if key in DEMO_CATEGORIES:
                cat = DEMO_CATEGORIES[key]
                cat_name = cat.names.get(lang, cat.names["en"])
                with quick_cols[idx]:
                    if st.button(
                        f"{cat.icon} {cat_name}", key=f"quick_{key}", use_container_width=True
                    ):
                        st.session_state.selected_demo_category = key

        # Compact dropdown for all categories
        groups = get_categories_by_group(lang)
        all_categories = []
        for group_name, categories in groups.items():
            for cat in categories:
                cat_name = cat.names.get(lang, cat.names["en"])
                all_categories.append(
                    (f"{cat.icon} {cat_name} ({len(cat.symbols)})", cat.key, group_name)
                )

        # Group selector + category selector in one row
        col1, col2 = st.columns([1, 2])
        with col1:
            group_names = list(groups.keys())
            selected_group = st.selectbox("📁", group_names, index=0, label_visibility="collapsed")

        with col2:
            # Get categories for selected group
            group_cats = groups.get(selected_group, [])
            cat_options = [
                f"{c.icon} {c.names.get(lang, c.names['en'])} ({len(c.symbols)})"
                for c in group_cats
            ]
            cat_keys = [c.key for c in group_cats]

            if cat_options:
                selected_idx = st.selectbox(
                    "🎯",
                    range(len(cat_options)),
                    format_func=lambda i: cat_options[i],
                    index=0,
                    label_visibility="collapsed",
                )
                if st.button(t("analyze"), key="analyze_btn", type="primary"):
                    st.session_state.selected_demo_category = cat_keys[selected_idx]

        # Show selected category
        if "selected_demo_category" in st.session_state:
            cat_key = st.session_state.selected_demo_category
            if cat_key in DEMO_CATEGORIES:
                cat = DEMO_CATEGORIES[cat_key]
                cat_name = cat.names.get(lang, cat.names["en"])
                cat_desc = cat.descriptions.get(lang, cat.descriptions["en"])
                st.success(f"✅ **{cat_name}** • {len(cat.symbols)} {t('stocks')} • {cat_desc}")
                return cat.symbols
        return None
    except ImportError:
        st.warning("Demo presets not available")
        return None


def render_feature_comparison():
    st.markdown(f"### {t('demo_vs_pro')}")
    col1, col2 = st.columns(2)
    with col1:
        features = "".join(f"<li>{f}</li>" for f in t_list("demo_features"))
        st.markdown(
            f"""
        <div class="waitlist-card">
            <span class="demo-badge">DEMO</span>
            <h4 style="color: #f8fafc; margin-top: 15px;">{t("free_demo")}</h4>
            <ul style="color: #cbd5f5;">{features}</ul>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        features = "".join(f"<li>{f}</li>" for f in t_list("pro_features_list"))
        st.markdown(
            f"""
        <div class="waitlist-card" style="border-color: #00e6e6;">
            <span class="pro-badge">PRO</span>
            <h4 style="color: #00e6e6; margin-top: 15px;">{t("finpilot_pro")}</h4>
            <ul style="color: #cbd5f5;">{features}</ul>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_cta_section():
    st.markdown("---")
    st.markdown(
        f"""
    <div style='background: linear-gradient(90deg, rgba(0,230,230,0.1) 0%, rgba(14,165,233,0.1) 100%);
                padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #00e6e6;'>
        <h2 style='color: #f8fafc;'>{t("ready_for_pro")}</h2>
        <p style='color: #cbd5f5; font-size: 1.1em;'>{t("cta_desc")}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("cta_waitlist", clear_on_submit=True):
            email = st.text_input(
                t("email"), placeholder=t("email_placeholder"), label_visibility="collapsed"
            )
            if st.form_submit_button(
                t("join_early_access"), use_container_width=True, type="primary"
            ):
                if email and "@" in email:
                    if save_to_waitlist(email, source="cta"):
                        st.success(t("cta_success"))
                        st.balloons()
                    else:
                        st.info(t("cta_already"))
                else:
                    st.error(t("cta_error"))


def render_footer():
    st.markdown("---")
    st.markdown(
        f"""
    <div style='text-align: center; color: #64748b; padding: 20px;'>
        <p>{t("copyright")}</p>
        <p style='font-size: 12px;'>{t("disclaimer")}</p>
        <p style='font-size: 12px;'>
            <a href="#" style="color: #00e6e6;">{t("privacy")}</a> |
            <a href="#" style="color: #00e6e6;">{t("terms")}</a> |
            <a href="#" style="color: #00e6e6;">{t("contact")}</a>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ============================================
# 🚀 MAIN APPLICATION
# ============================================


def main():
    # Initialize language (English default)
    if "language" not in st.session_state:
        st.session_state.language = "en"

    render_signup_banner()
    render_language_selector()
    render_waitlist_sidebar()

    selected_symbols = render_category_selector()
    if selected_symbols:
        st.session_state.demo_symbols = selected_symbols

    try:
        from views.demo import render_demo_page

        render_demo_page(standalone=True)
    except Exception as e:
        st.error(t("demo_error", error=str(e)))
        st.info(t("demo_retry"))

    render_feature_comparison()
    render_cta_section()
    render_footer()


if __name__ == "__main__":
    main()
