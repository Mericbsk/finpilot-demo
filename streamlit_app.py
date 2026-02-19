import streamlit as st
from views.styles import GLOBAL_CSS

# Auth imports
from auth import get_session_manager, render_auth_page, render_user_profile

# Set page configuration
st.set_page_config(
    page_title="FinPilot - AI Trading Platform",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded",
)

# Inject Global CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Initialize auth session manager
session_mgr = get_session_manager()

# Navigation in sidebar
PAGES = {
    "🏠 Ana Panel": "panel",
    "🎯 Demo": "demo",
    "🎓 FinSense Akademi": "finsense",
    "📜 Geçmiş": "history",
}

# Pages that require authentication
PROTECTED_PAGES = {"panel", "history"}
# Public pages (no auth required)
PUBLIC_PAGES = {"demo", "finsense"}

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "panel"

# Sidebar navigation
st.sidebar.title("🚀 FinPilot")

# Show user info if authenticated
if session_mgr.is_authenticated:
    user = session_mgr.current_user
    if user:
        st.sidebar.success(f"👤 {user.display_name or user.username}")
        if st.sidebar.button("🚪 Çıkış Yap", key="logout_btn"):
            session_mgr.logout()
            st.rerun()
else:
    st.sidebar.info("🔐 Giriş yapın veya kayıt olun")

st.sidebar.markdown("---")

# Get current index
page_keys = list(PAGES.values())
current_index = (
    page_keys.index(st.session_state.current_page)
    if st.session_state.current_page in page_keys
    else 0
)

selected_page = st.sidebar.radio(
    "Sayfa Seçin", list(PAGES.keys()), index=current_index, key="nav_radio"
)

# Update current page based on selection
st.session_state.current_page = PAGES[selected_page]

st.sidebar.markdown("---")
st.sidebar.caption("v1.7.0 | FinPilot Team")

# Render the selected page
if __name__ == "__main__":
    page = st.session_state.current_page

    # Check if page requires authentication
    requires_auth = page in PROTECTED_PAGES
    is_authenticated = session_mgr.is_authenticated

    # Public pages - no auth required
    if page == "demo":
        from views.demo import render_demo_page

        render_demo_page()

    elif page == "finsense":
        from views.finsense import render_finsense_page

        render_finsense_page()

    # Protected pages - require authentication
    elif page == "history":
        if not is_authenticated:
            st.warning("📜 Geçmiş sayfasını görüntülemek için giriş yapmalısınız.")
            render_auth_page(session_mgr)
        else:
            from views.history import render_history_page

            render_history_page()

    else:
        # Ana Panel - Dashboard (Protected)
        if not is_authenticated:
            # First show landing for new visitors, then auth
            if not st.session_state.get("has_seen_landing", False):
                from views.landing import render_finpilot_landing

                render_finpilot_landing()
            else:
                # Landing seen, show auth page
                st.info("🔐 Tarama paneline erişmek için giriş yapın veya kayıt olun.")

                # Quick access to demo
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🎯 Demo'yu Dene", use_container_width=True):
                        st.session_state.current_page = "demo"
                        st.rerun()

                render_auth_page(session_mgr)
        else:
            # Authenticated - show scanner
            from views.dashboard import render_scanner_page

            # Show user profile in sidebar
            with st.sidebar:
                render_user_profile(session_mgr)

            # Render the scanner page
            render_scanner_page()
