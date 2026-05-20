"""
FinPilot Onboarding Wizard
==========================

Step-by-step introduction for new users.
Guides users through key features and initial setup.

Usage:
    from views.components.onboarding import render_onboarding, should_show_onboarding

    if should_show_onboarding():
        render_onboarding()
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# ============================================
# 📋 Onboarding Configuration
# ============================================

ONBOARDING_KEY = "finpilot_onboarding"
ONBOARDING_FILE = "data/onboarding_status.json"

# Onboarding steps
ONBOARDING_STEPS = [
    {
        "id": "welcome",
        "title": "FinPilot'a Hoş Geldiniz! 🚀",
        "icon": "👋",
        "content": """
        **FinPilot**, yapay zeka destekli hisse senedi tarama ve analiz sistemidir.

        Bu kısa tanıtım, temel özellikleri keşfetmenize yardımcı olacak.

        **Ne yapabilirsiniz?**
        - 📊 Piyasayı gerçek zamanlı tarayın
        - 🎯 Al/Sat sinyallerini analiz edin
        - 🧠 AI ile derinlemesine araştırma yapın
        - 📋 Favori hisselerinizi izleyin
        """,
        "action": None,
    },
    {
        "id": "scanner",
        "title": "Piyasa Tarayıcısı 🔍",
        "icon": "🔍",
        "content": """
        **Tarayıcı**, tüm piyasayı analiz ederek en iyi fırsatları bulur.

        **Nasıl kullanılır?**
        1. Sol panelden ayarları yapın
        2. "Taramayı Başlat" butonuna tıklayın
        3. Sonuçları inceleyip detaylı analize geçin

        **Pro İpucu:** Agresif Mod'u açarak daha fazla fırsat görebilirsiniz.
        """,
        "action": "scan_demo",
    },
    {
        "id": "signals",
        "title": "Sinyal Kartları 🎯",
        "icon": "🎯",
        "content": """
        **Sinyal kartları**, her hisse için alım/satım önerilerini gösterir.

        **Kart bilgileri:**
        - 📈 **Sinyal Gücü:** 0-100 arası puan
        - 🎯 **Hedef (TP):** Kar alma seviyesi
        - ⛔ **Stop (SL):** Zarar durdurma seviyesi
        - 📊 **Rejim:** Piyasa durumu (Bull/Bear)

        **Pro İpucu:** Yeşil kartlar güçlü alım sinyallerini gösterir.
        """,
        "action": None,
    },
    {
        "id": "watchlist",
        "title": "İzleme Listesi 📋",
        "icon": "📋",
        "content": """
        **İzleme listesi**, favori hisselerinizi takip etmenizi sağlar.

        **Özellikler:**
        - ➕ Sembol ekle/çıkar
        - 🔍 Sadece listedeki sembolleri tara
        - 📥 CSV olarak dışa aktar
        - 💾 Otomatik kayıt

        **Erişim:** Sol panelde "İzleme Listesi" bölümü.
        """,
        "action": "open_watchlist",
    },
    {
        "id": "ai_lab",
        "title": "AI Laboratuvarı 🧠",
        "icon": "🧠",
        "content": """
        **AI Lab**, seçtiğiniz hisse için derin analiz yapar.

        **Sağlanan bilgiler:**
        - 📰 Güncel haberler ve yorumlar
        - 📊 Teknik analiz özeti
        - 🎯 AI önerileri ve risk değerlendirmesi
        - 🔮 Kısa/orta vadeli beklentiler

        **Kullanım:** Bir sinyal kartından "AI Analizi" butonuna tıklayın.
        """,
        "action": None,
    },
    {
        "id": "complete",
        "title": "Hazırsınız! 🎉",
        "icon": "🎉",
        "content": """
        Tebrikler! Temel özellikleri öğrendiniz.

        **Sonraki adımlar:**
        - 🔍 İlk taramanızı yapın
        - 📋 Birkaç favori hisse ekleyin
        - 🧠 AI analizlerini keşfedin

        **Yardım:** Her zaman "?" simgelerinden ek bilgi alabilirsiniz.

        FinPilot ile başarılar dileriz! 📈
        """,
        "action": "start_scan",
    },
]


# ============================================
# 💾 Onboarding Persistence
# ============================================


def _load_onboarding_status() -> dict[str, Any]:
    """Load onboarding status from file."""
    try:
        path = Path(ONBOARDING_FILE)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        logging.getLogger(__name__).warning("Failed to load onboarding status", exc_info=True)
    return {"completed": False, "current_step": 0, "skipped": False}


def _save_onboarding_status(status: dict[str, Any]) -> None:
    """Save onboarding status to file."""
    try:
        path = Path(ONBOARDING_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        status["updated_at"] = datetime.now().isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.getLogger(__name__).warning("Failed to save onboarding status", exc_info=True)


def get_onboarding_state() -> dict[str, Any]:
    """Get current onboarding state from session or file."""
    if ONBOARDING_KEY not in st.session_state:
        st.session_state[ONBOARDING_KEY] = _load_onboarding_status()
    return st.session_state[ONBOARDING_KEY]


def set_onboarding_step(step: int) -> None:
    """Set current onboarding step."""
    state = get_onboarding_state()
    state["current_step"] = step
    st.session_state[ONBOARDING_KEY] = state
    _save_onboarding_status(state)


def complete_onboarding() -> None:
    """Mark onboarding as completed."""
    state = get_onboarding_state()
    state["completed"] = True
    state["completed_at"] = datetime.now().isoformat()
    st.session_state[ONBOARDING_KEY] = state
    _save_onboarding_status(state)


def skip_onboarding() -> None:
    """Skip onboarding."""
    state = get_onboarding_state()
    state["skipped"] = True
    state["completed"] = True
    st.session_state[ONBOARDING_KEY] = state
    _save_onboarding_status(state)


def reset_onboarding() -> None:
    """Reset onboarding to start fresh."""
    state = {"completed": False, "current_step": 0, "skipped": False}
    st.session_state[ONBOARDING_KEY] = state
    _save_onboarding_status(state)


def should_show_onboarding() -> bool:
    """Check if onboarding should be shown."""
    state = get_onboarding_state()
    return not state.get("completed", False) and not state.get("skipped", False)


# ============================================
# 🎨 Onboarding UI
# ============================================


def render_onboarding_modal() -> None:
    """Render onboarding as a modal dialog."""
    state = get_onboarding_state()
    current_step = state.get("current_step", 0)

    if current_step >= len(ONBOARDING_STEPS):
        complete_onboarding()
        return

    step = ONBOARDING_STEPS[current_step]
    total_steps = len(ONBOARDING_STEPS)

    # Modal container
    st.markdown(
        """
    <style>
    .onboarding-modal {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        max-width: 600px;
        margin: 2rem auto;
    }
    .onboarding-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .onboarding-icon {
        font-size: 3rem;
    }
    .onboarding-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .onboarding-content {
        color: #cbd5e1;
        line-height: 1.7;
    }
    .onboarding-progress {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .onboarding-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #334155;
    }
    .onboarding-dot.active {
        background: #3b82f6;
    }
    .onboarding-dot.completed {
        background: #22c55e;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Progress dots
    dots_html = ""
    for i in range(total_steps):
        if i < current_step:
            dots_html += '<span class="onboarding-dot completed"></span>'
        elif i == current_step:
            dots_html += '<span class="onboarding-dot active"></span>'
        else:
            dots_html += '<span class="onboarding-dot"></span>'

    st.markdown(
        f"""
    <div class="onboarding-modal">
        <div class="onboarding-progress">{dots_html}</div>
        <div class="onboarding-header">
            <span class="onboarding-icon">{step["icon"]}</span>
            <h2 class="onboarding-title">{step["title"]}</h2>
        </div>
        <div class="onboarding-content">
            {step["content"].replace(chr(10), "<br/>")}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_step > 0:
            if st.button("⬅️ Geri", key="onboarding_back", use_container_width=True):
                set_onboarding_step(current_step - 1)
                st.rerun()

    with col2:
        if st.button("⏭️ Atla", key="onboarding_skip"):
            skip_onboarding()
            st.rerun()

    with col3:
        if current_step < total_steps - 1:
            if st.button(
                "İleri ➡️", key="onboarding_next", use_container_width=True, type="primary"
            ):
                set_onboarding_step(current_step + 1)
                st.rerun()
        else:
            if st.button(
                "Başla! 🚀", key="onboarding_complete", use_container_width=True, type="primary"
            ):
                complete_onboarding()
                st.rerun()


def render_onboarding_sidebar_trigger() -> None:
    """Render a button in sidebar to restart onboarding."""
    with st.sidebar:
        if st.button("❓ Kullanım Rehberi", key="show_onboarding_guide"):
            reset_onboarding()
            st.rerun()


def render_quick_tips() -> None:
    """Render quick tips for experienced users."""
    tips = [
        "💡 **İpucu:** Sembol üzerine tıklayarak detaylı analiz görün.",
        "💡 **İpucu:** Agresif Mod daha fazla sinyal üretir.",
        "💡 **İpucu:** İzleme listesini CSV olarak dışa aktarabilirsiniz.",
        "💡 **İpucu:** AI Lab'da hisse hakkında derin analiz yapın.",
    ]

    import random

    tip = random.choice(tips)
    st.caption(tip)


def render_feature_highlight(feature: str) -> None:
    """
    Highlight a specific feature with a tooltip.

    Args:
        feature: Feature name to highlight
    """
    feature_tips = {
        "scanner": "🔍 Tarayıcı: Tüm piyasayı tek tıkla analiz edin.",
        "watchlist": "📋 İzleme Listesi: Favori hisselerinizi buradan yönetin.",
        "export": "📥 Dışa Aktar: Sonuçları CSV/Excel/PDF olarak indirin.",
        "ai_lab": "🧠 AI Lab: Derin analiz için bu sekmeyi kullanın.",
    }

    tip = feature_tips.get(feature, "")
    if tip:
        st.info(tip)


__all__ = [
    "ONBOARDING_STEPS",
    "should_show_onboarding",
    "render_onboarding_modal",
    "render_onboarding_sidebar_trigger",
    "render_quick_tips",
    "render_feature_highlight",
    "complete_onboarding",
    "skip_onboarding",
    "reset_onboarding",
    "get_onboarding_state",
]
