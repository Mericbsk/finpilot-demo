import streamlit as st
from views.styles import GLOBAL_CSS
from views.demo import render_demo_page

# Set page configuration
st.set_page_config(
    page_title="FinPilot Global Demo",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Inject Global CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Render the Demo Page
if __name__ == "__main__":
    render_demo_page()
