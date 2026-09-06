"""
SemiVision - Secondary Navigation Views
Provides implementations for Wafer Map Explorer, FAB Yield Analytics, 
Inspection History Logs, AI Model Pipeline Architecture, and System Settings.
"""

import streamlit as st
import pandas as pd
from utils.mock_data import (
    get_recent_inspections, 
    get_mini_wafer_defects,
    get_yield_trend_data,
    get_defect_type_distribution,
    get_severity_distribution,
    get_defects_per_wafer_data,
    get_spatial_pattern_data,
    get_model_pipeline_info
)
from utils.visualization import (
    create_wafer_map,
    create_yield_trend_chart,
    create_defect_bar_chart,
    create_severity_pie_chart,
    create_defects_per_wafer_hist,
    create_spatial_pattern_bar
)

def render_wafer_map():
    """Renders standalone 300mm Wafer Map Explorer."""
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">⭕ 300mm Wafer Spatial Pattern Explorer</div>
                <div class="hero-subtitle">Interactive cartesian defect mapping & die matrix spatial pattern analysis</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse"></span>
                    <span>● SPATIAL ENGINE ACTIVE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🎛️ Wafer Selector & Filters</div>
        """, unsafe_allow_html=True)
        st.selectbox("Select Lot ID", ["LOT-884A (Active)", "LOT-883F", "LOT-882C", "LOT-881B"])
        st.selectbox("Select Wafer Serial", ["W-300-9841 (Edge Scratch)", "W-300-9839 (Particle Cluster)", "W-300-9838 (Center Pattern)"])
        st.multiselect("Filter Defect Categories", ["Scratch", "Particle", "Edge-Loc", "Center", "Donut", "Random", "Other"], default=["Scratch", "Particle"])
        
        st.markdown("""
            <div style="background: rgba(14, 18, 27, 0.6); padding: 12px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5); font-size: 12px; margin-top: 12px;">
                <div style="color: #00F0FF; font-weight: 600; margin-bottom: 4px;">Spatial Pattern Analysis</div>
                <div style="color: #94A3B8; line-height: 1.5;">
                    • Total Defects: <code>5</code><br>
                    • Pattern: <strong>Edge concentration</strong><br>
                    • Substrate Sector: Periphery Notch (Die 14B)
                </div>
                <div style="font-size: 10px; color: #64748B; margin-top: 8px; font-style: italic;">
                    ⚠️ Spatial patterns represent statistical AI clustering for process clues and do not prove manufacturing root cause.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">⭕ 300mm Circular Wafer Plot</div>
        """, unsafe_allow_html=True)
        defects = get_mini_wafer_defects()
        fig = create_wafer_map(defects, title="300mm Die Matrix & Color-Coded Defect Coordinates Overlay")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_analytics():
    """Renders FAB Yield Analytics view."""
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">📈 FAB Yield & Quality Analytics</div>
                <div class="hero-subtitle">Process control trends, Pareto defect rankings, and spatial pattern statistics</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse"></span>
                    <span>● ANALYTICS ACTIVE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Row 1: Yield Trend & Defects per Wafer
    r1_c1, r1_c2 = st.columns([1.1, 0.9])
    
    with r1_c1:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">📈 14-Day FAB Yield Pass Rate Trend</div>
        """, unsafe_allow_html=True)
        df_trend = get_yield_trend_data()
        fig_trend = create_yield_trend_chart(df_trend)
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with r1_c2:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">📊 Defect Frequency per Wafer</div>
        """, unsafe_allow_html=True)
        df_hist = get_defects_per_wafer_data()
        fig_hist = create_defects_per_wafer_hist(df_hist)
        st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Row 2: Pareto Distribution, Severity Pie & Spatial Patterns
    r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
    
    with r2_c1:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🔍 Defect Category Distribution</div>
        """, unsafe_allow_html=True)
        df_defects = get_defect_type_distribution()
        fig_bar = create_defect_bar_chart(df_defects)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with r2_c2:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🎯 Severity Band Distribution</div>
        """, unsafe_allow_html=True)
        df_sev = get_severity_distribution()
        fig_pie = create_severity_pie_chart(df_sev)
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with r2_c3:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🧠 Spatial Pattern Statistics</div>
        """, unsafe_allow_html=True)
        df_sp = get_spatial_pattern_data()
        fig_sp = create_spatial_pattern_bar(df_sp)
        st.plotly_chart(fig_sp, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

def render_history():
    """Renders Inspection History Logs view."""
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">📜 Comprehensive Inspection History</div>
                <div class="hero-subtitle">Historical audit log trail of automated semiconductor wafer inspection decisions</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse"></span>
                    <span>● LOG STREAM ONLINE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="glass-panel-card">
            <div class="panel-header-title">🔍 Search & Audit Log Trail</div>
    """, unsafe_allow_html=True)

    df_hist = get_recent_inspections()
    
    col_search, col_filter, col_dl = st.columns([0.4, 0.3, 0.3])
    with col_search:
        search_query = st.text_input("Search by Wafer ID or Lot ID", value="")
    with col_filter:
        decision_filter = st.selectbox("Filter Decision", ["All Decisions", "PASS", "REVIEW", "FAIL"])
    with col_dl:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        csv_bytes = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export History CSV", data=csv_bytes, file_name="SemiVision_Inspection_History.csv", mime="text/csv", use_container_width=True)

    filtered_df = df_hist.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Wafer ID"].str.contains(search_query, case=False) | 
            filtered_df["Lot ID"].str.contains(search_query, case=False)
        ]
    if decision_filter != "All Decisions":
        filtered_df = filtered_df[filtered_df["Decision"] == decision_filter]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Severity": st.column_config.ProgressColumn(min_value=0, max_value=100),
            "Confidence": st.column_config.NumberColumn(format="%.3f")
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

def render_model_info():
    """Renders AI Model Pipeline Architecture view with honest pending integration notices."""
    pipeline_info = get_model_pipeline_info()
    
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">🧠 SemiVision AI Pipeline Architecture</div>
                <div class="hero-subtitle">Current inspection pipeline specification, model integration status, and API contract schema</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse" style="background-color: #00F0FF; box-shadow: 0 0 10px #00F0FF;"></span>
                    <span style="color: #00F0FF;">API-READY ARCHITECTURE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.55, 0.45])
    
    with col1:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">⚙️ Current AI Inspection Pipeline Stages</div>
        """, unsafe_allow_html=True)

        for stage in pipeline_info["pipeline_stages"]:
            status_color = "#10B981" if stage["status"] == "Ready" else "#F59E0B"
            st.markdown(f"""
                <div style="background: rgba(14, 18, 27, 0.6); padding: 12px 16px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5); margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="font-weight: 700; color: #00F0FF; font-family: 'JetBrains Mono'; margin-right: 8px;">{stage['step']}.</span>
                        <span style="font-weight: 600; color: #FFFFFF;">{stage['name']}</span>
                        <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">{stage['tech']}</div>
                    </div>
                    <span style="font-size: 10px; font-weight: 700; color: {status_color}; font-family: 'JetBrains Mono'; background: rgba(0,240,255,0.08); padding: 4px 8px; border-radius: 4px; border: 1px solid {status_color};">
                        {stage['status']}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">📊 Model Evaluation Metrics</div>
                <div class="proto-disclaimer-card" style="margin-top: 0;">
                    ℹ️ <strong>Training Status Notice:</strong><br>
                    Model evaluation metrics (mAP, Precision, Recall, F1) will be populated after formal model training and validation on full FAB dataset.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="glass-panel-card">
                <div class="panel-header-title">🌐 REST API Endpoint Contract</div>
                <div style="font-size: 12px; color: #F8FAFC; line-height: 1.6;">
                    <p><strong>Target Endpoint:</strong> <code>{pipeline_info['api_endpoint']}</code></p>
                    <p><strong>HTTP Method:</strong> <code>POST</code></p>
                    <p><strong>Expected Output Contract:</strong></p>
                    <pre style="background: rgba(14, 18, 27, 0.85); padding: 12px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5); color: #00F0FF; font-size: 11px;">
{{
    "primary_defect": "Scratch",
    "confidence": 0.968,
    "defect_count": 5,
    "severity": 78,
    "decision": "REVIEW",
    "spatial_pattern": "Edge concentration",
    "recommendation": "Hold wafer for engineer review.",
    "defects": [...]
}}</pre>
                </div>
            </div>
        """, unsafe_allow_html=True)

def render_settings():
    """Renders System Settings view."""
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">⚙️ System Settings & Preferences</div>
                <div class="hero-subtitle">Configure decision threshold parameters, confidence bounds, and API connections</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse"></span>
                    <span>● SETTINGS ACTIVE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.5, 0.5])
    
    with col1:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🎚️ Decision Threshold Settings</div>
        """, unsafe_allow_html=True)
        st.slider("PASS Threshold Upper Bound (0-30 = PASS)", 0, 50, 30)
        st.slider("REVIEW Threshold Upper Bound (31-60 = REVIEW)", 30, 80, 60)
        st.slider("Minimum Confidence Threshold (%)", 50, 99, 85)
        st.markdown("<div style='font-size: 11px; color: #94A3B8; margin-top: 8px;'>Scores above upper REVIEW bound trigger CRITICAL / FAIL decision.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🌐 Backend API Connection</div>
        """, unsafe_allow_html=True)
        api_url = st.text_input("Backend REST API Endpoint", value="http://localhost:8000/api/v1/analyze")
        st.checkbox("Enable Demo Mode (Mock Analyzer)", value=True)
        
        if st.button("🔌 Test API Connection"):
            st.info(f"Pinging endpoint `{api_url}`... (Mock Analyzer active, ready for live API backend integration)")
            
        st.markdown("</div>", unsafe_allow_html=True)
