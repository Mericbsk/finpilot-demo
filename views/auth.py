"""
Authentication View for FinPilot Streamlit App.

Provides authentication pages and protected route handling.
"""

from __future__ import annotations

import streamlit as st

from auth import (
    get_session_manager,
    render_auth_page,
    render_settings_panel,
)


def render_auth_sidebar() -> None:
    """Render authentication info in sidebar."""
    session_mgr = get_session_manager()

    if session_mgr.is_authenticated:
        user = session_mgr.current_user

        # Early return if user is None
        if user is None:
            return

        with st.sidebar:
            st.markdown("---")

            # User info
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(
                    f"""
                    <div style='
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 18px;
                        color: white;
                    '>
                        {user.username[0].upper()}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(f"**{user.display_name or user.username}**")
                st.caption(user.email)

            # Portfolio summary
            portfolio = session_mgr.user_portfolio
            if portfolio:
                st.markdown("---")
                st.caption("📊 Portföy Özeti")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Nakit", f"${portfolio.cash:,.2f}")
                with col2:
                    st.metric("Pozisyon", str(portfolio.position_count))

            # Logout button
            st.markdown("---")
            if st.button("🚪 Çıkış Yap", use_container_width=True, key="sidebar_logout"):
                session_mgr.logout()
                st.rerun()
    else:
        with st.sidebar:
            st.markdown("---")
            st.info("🔐 Giriş yapın veya kayıt olun")


def protected_page(title: str = "FinPilot"):
    """
    Decorator for protected pages.

    Usage:
        @protected_page("Dashboard")
        def show_dashboard():
            st.write("Protected content")
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            session_mgr = get_session_manager()
            session_mgr.initialize()

            if not session_mgr.is_authenticated:
                render_auth_page(session_mgr)
                return None

            if not session_mgr.verify_session():
                st.warning("Oturumunuz sona erdi. Lütfen tekrar giriş yapın.")
                render_auth_page(session_mgr)
                return None

            # Render sidebar auth info
            render_auth_sidebar()

            # Render page
            return func(*args, **kwargs)

        return wrapper

    return decorator


def show_auth_page() -> None:
    """Show authentication page."""
    session_mgr = get_session_manager()
    session_mgr.initialize()
    render_auth_page(session_mgr)


def show_profile_page() -> None:
    """Show user profile page."""
    session_mgr = get_session_manager()

    if not session_mgr.is_authenticated:
        st.warning("Bu sayfayı görüntülemek için giriş yapmalısınız.")
        render_auth_page(session_mgr)
        return

    st.title("👤 Profilim")

    user = session_mgr.current_user

    # Guard against None user
    if user is None:
        st.error("Kullanıcı bilgisi yüklenemedi.")
        return

    # Profile header
    col1, col2 = st.columns([1, 4])

    with col1:
        st.markdown(
            f"""
            <div style='
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 48px;
                color: white;
                margin: 10px 0;
            '>
                {user.username[0].upper()}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.subheader(user.display_name or user.username)
        st.caption(f"📧 {user.email}")
        st.caption(f"👤 @{user.username}")
        st.caption(f"📅 Üyelik: {user.created_at.strftime('%d %B %Y')}")
        st.caption(f"🏷️ Rol: {user.role.value.title()}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ Ayarlar", "📊 Portföy", "🔒 Güvenlik"])

    with tab1:
        render_settings_panel(session_mgr)

    with tab2:
        portfolio = session_mgr.user_portfolio
        if portfolio:
            st.metric("Nakit Bakiye", f"${portfolio.cash:,.2f}")
            st.metric("Toplam Pozisyon", portfolio.position_count)

            if portfolio.positions:
                st.markdown("#### Pozisyonlar")
                for pos in portfolio.positions:
                    st.write(f"**{pos.symbol}**: {pos.shares} hisse @ ${pos.avg_price:.2f}")
            else:
                st.info("Henüz açık pozisyonunuz yok.")

    with tab3:
        st.markdown("#### Şifre Değiştir")
        with st.form("change_password"):
            old_pass = st.text_input("Mevcut Şifre", type="password")
            new_pass = st.text_input("Yeni Şifre", type="password")
            confirm_pass = st.text_input("Yeni Şifre (Tekrar)", type="password")

            if st.form_submit_button("Şifreyi Değiştir"):
                if new_pass != confirm_pass:
                    st.error("Yeni şifreler eşleşmiyor")
                elif len(new_pass) < 8:
                    st.error("Şifre en az 8 karakter olmalı")
                else:
                    try:
                        session_mgr.auth.change_password(user.id, old_pass, new_pass)
                        st.success("Şifreniz başarıyla değiştirildi!")
                    except Exception as e:
                        st.error(f"Hata: {e}")

        st.markdown("---")
        st.markdown("#### Oturum Yönetimi")

        if st.button("📱 Tüm Cihazlardan Çıkış Yap"):
            session_mgr.auth.logout_all(user.id)
            session_mgr.logout()
            st.success("Tüm oturumlar kapatıldı")
            st.rerun()


def is_authenticated() -> bool:
    """Check if current user is authenticated."""
    session_mgr = get_session_manager()
    session_mgr.initialize()
    return session_mgr.is_authenticated


def get_current_user():
    """Get current authenticated user."""
    session_mgr = get_session_manager()
    return session_mgr.current_user


__all__ = [
    "render_auth_sidebar",
    "protected_page",
    "show_auth_page",
    "show_profile_page",
    "is_authenticated",
    "get_current_user",
]
