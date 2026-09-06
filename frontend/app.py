"""
SemiVision - AI Semiconductor Manufacturing Inspection Platform
Main Streamlit Application Entry Point
"""

import streamlit as st
import os

# 1. Page Configuration
st.set_page_config(
    page_title="SemiVision | AI Semiconductor Inspection",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Dark Futuristic Engineering CSS
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# 3. Import View Modules
from views.dashboard import render_dashboard
from views.inspection import render_inspection
from views.placeholders import (
    render_wafer_map,
    render_analytics,
    render_history,
    render_model_info,
    render_settings
)

# 4. Sidebar Branding & Navigation
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; border-bottom: 1px solid rgba(42, 53, 80, 0.6); margin-bottom: 16px;">
            <div style="font-size: 22px; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                <span style="color: #00F0FF;">⚡</span> SemiVision
            </div>
            <div style="font-size: 11px; color: #94A3B8; margin-top: 4px; font-weight: 500;">
                AI Semiconductor Inspection & Quality Intelligence
            </div>
            <div style="margin-top: 10px; display: flex; align-items: center; gap: 8px;">
                <span style="display:inline-block; width:8px; height:8px; background:#10B981; border-radius:50%; box-shadow:0 0 8px #10B981;"></span>
                <span style="font-size:11px; font-weight:600; color:#10B981; font-family:'JetBrains Mono';">● SYSTEM ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    selected_page = st.radio(
        "Navigation Menu",
        options=[
            "Dashboard",
            "Inspection",
            "Wafer Map",
            "Analytics",
            "Inspection History",
            "Model Information",
            "Settings"
        ],
        format_func=lambda x: {
            "Dashboard": "📊  Dashboard",
            "Inspection": "🔬  Inspection",
            "Wafer Map": "⭕  Wafer Map",
            "Analytics": "📈  Analytics",
            "Inspection History": "📜  Inspection History",
            "Model Information": "🧠  Model Information",
            "Settings": "⚙️  Settings"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("""
        <div style="padding: 12px; background: rgba(14, 18, 27, 0.6); border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5); font-size: 11px; color: #94A3B8;">
            <div style="color: #00F0FF; font-weight: 600; margin-bottom: 4px;">Prototype Architecture</div>
            Decoupled mock analysis engine active. API-ready for backend integration.
        </div>
    """, unsafe_allow_html=True)

# 5. Route Navigation
if selected_page == "Dashboard":
    render_dashboard()
elif selected_page == "Inspection":
    render_inspection()
elif selected_page == "Wafer Map":
    render_wafer_map()
elif selected_page == "Analytics":
    render_analytics()
elif selected_page == "Inspection History":
    render_history()
elif selected_page == "Model Information":
    render_model_info()
elif selected_page == "Settings":
    render_settings()
