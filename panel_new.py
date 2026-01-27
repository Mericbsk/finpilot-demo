import streamlit as st

from views.dashboard import render_scanner_page
from views.finsense import render_finsense_page
from views.history import render_history_page
from views.landing import render_finpilot_landing
from views.settings import render_settings_page
from views.styles import GLOBAL_CSS

st.set_page_config(page_title="FinPilot Panel", layout="wide", page_icon="🛫")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if "show_demo" not in st.session_state:
    st.session_state.show_demo = False

if st.session_state.show_demo:
    from views.demo import render_demo_page

    render_demo_page()
    st.stop()

if "has_seen_landing" not in st.session_state:
    st.session_state.has_seen_landing = False

if not st.session_state.has_seen_landing:
    render_finpilot_landing()

# Sidebar Navigation
page = st.sidebar.selectbox(
    "Sayfa Seç", ["Panel", "FinSense Akademi", "Kişiselleştirme", "Geçmiş Sinyaller"]
)

if page == "Panel":
    render_scanner_page()
elif page == "FinSense Akademi":
    render_finsense_page()
elif page == "Kişiselleştirme":
    render_settings_page()
elif page == "Geçmiş Sinyaller":
    render_history_page()
