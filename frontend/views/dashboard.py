"""
SemiVision - Dashboard View
Main overview interface displaying branding, system status panel, KPI metrics, defect distributions, recent inspection logs, and mini wafer map.
"""

import streamlit as st
import pandas as pd
from utils.mock_data import (
    get_dashboard_kpis, 
    get_system_status,
    get_defect_type_distribution, 
    get_severity_distribution, 
    get_recent_inspections,
    get_mini_wafer_defects
)
from utils.visualization import (
    create_wafer_map, 
    create_defect_bar_chart, 
    create_severity_pie_chart
)

def render_dashboard():
    """Renders the main SemiVision Dashboard."""
    
    # 1. Hero Header Banner
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">
                    <span>⚡ SemiVision</span>
                    <span style="font-size:12px; font-weight:500; color:#00F0FF; background:rgba(0,240,255,0.1); padding:4px 10px; border-radius:12px; border:1px solid rgba(0,240,255,0.3);">
                        FAB-1 LINE 4
                    </span>
                </div>
                <div class="hero-subtitle">AI Semiconductor Inspection & Quality Intelligence</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse"></span>
                    <span>● SYSTEM ONLINE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. System Status Panel
    sys_status = get_system_status()
    st.markdown("""
        <div class="glass-panel-card" style="padding: 14px 20px; margin-bottom: 20px;">
            <div class="panel-header-title" style="margin-bottom: 10px; padding-bottom: 6px; font-size: 13px;">
                <span>🖥️ System Operational Subsystems Status</span>
                <span style="font-size: 11px; color: #94A3B8; font-weight: 400;">Real-Time Health Ping</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    idx = 0
    for key, val in sys_status.items():
        with cols[idx]:
            st.markdown(f"""
                <div style="background: rgba(14, 18, 27, 0.6); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5); display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-size: 11px; color: #94A3B8;">{key}</div>
                        <div style="font-size: 12px; font-weight: 600; color: #FFFFFF;">{val['status']}</div>
                    </div>
                    <span style="font-size: 10px; font-weight: 700; color: {val['color']}; font-family: 'JetBrains Mono'; background: rgba(0,240,255,0.1); padding: 2px 6px; border-radius: 4px;">{val['badge']}</span>
                </div>
            """, unsafe_allow_html=True)
        idx += 1

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. KPI Cards Row
    kpis = get_dashboard_kpis()
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card-enterprise">
                <div class="metric-header">
                    <span class="metric-label-text">Total Inspections</span>
                    <span class="metric-icon-tag">{kpis['total_inspections']['icon']}</span>
                </div>
                <div class="metric-value-num">{kpis['total_inspections']['value']:,}</div>
                <div class="metric-footer-delta delta-positive">↑ {kpis['total_inspections']['delta']} <span style="color:#94A3B8;">{kpis['total_inspections']['period']}</span></div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-card-enterprise">
                <div class="metric-header">
                    <span class="metric-label-text">Defects Detected</span>
                    <span class="metric-icon-tag">{kpis['defects_detected']['icon']}</span>
                </div>
                <div class="metric-value-num">{kpis['defects_detected']['value']}</div>
                <div class="metric-footer-delta delta-positive">↓ {kpis['defects_detected']['delta']} <span style="color:#94A3B8;">{kpis['defects_detected']['period']}</span></div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="metric-card-enterprise">
                <div class="metric-header">
                    <span class="metric-label-text">Critical Defects</span>
                    <span class="metric-icon-tag">{kpis['critical_defects']['icon']}</span>
                </div>
                <div class="metric-value-num" style="color:#EF4444;">{kpis['critical_defects']['value']}</div>
                <div class="metric-footer-delta delta-negative">⚠️ {kpis['critical_defects']['delta']} <span style="color:#94A3B8;">{kpis['critical_defects']['period']}</span></div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="metric-card-enterprise">
                <div class="metric-header">
                    <span class="metric-label-text">Avg Severity</span>
                    <span class="metric-icon-tag">{kpis['avg_severity']['icon']}</span>
                </div>
                <div class="metric-value-num">{kpis['avg_severity']['value']}</div>
                <div class="metric-footer-delta delta-positive">↓ {kpis['avg_severity']['delta']} <span style="color:#94A3B8;">{kpis['avg_severity']['period']}</span></div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
            <div class="metric-card-enterprise">
                <div class="metric-header">
                    <span class="metric-label-text">Pass Rate</span>
                    <span class="metric-icon-tag">{kpis['pass_rate']['icon']}</span>
                </div>
                <div class="metric-value-num" style="color:#10B981;">{kpis['pass_rate']['value']}</div>
                <div class="metric-footer-delta delta-positive">↑ {kpis['pass_rate']['delta']} <span style="color:#94A3B8;">{kpis['pass_rate']['period']}</span></div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 4. Main Analytics Layout (2 Columns)
    left_col, right_col = st.columns([1.1, 0.9])
    
    with left_col:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">
                    <span>📊 Defect Category Distribution</span>
                    <span style="font-size:11px; color:#94A3B8; font-weight:400;">Categories: Scratch, Particle, Edge-Loc, Center, Donut, Random, Other</span>
                </div>
        """, unsafe_allow_html=True)
        
        df_defects = get_defect_type_distribution()
        fig_bar = create_defect_bar_chart(df_defects)
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">
                    <span>🎯 Severity Band Breakdown</span>
                    <span style="font-size:11px; color:#94A3B8; font-weight:400;">Prototype Decision Thresholds</span>
                </div>
        """, unsafe_allow_html=True)
        
        df_sev = get_severity_distribution()
        fig_pie = create_severity_pie_chart(df_sev)
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("""
            <div class="proto-disclaimer-card">
                <strong>Prototype Decision Thresholds:</strong> 🟢 <code>0–30 PASS</code> | 🟡 <code>31–60 REVIEW</code> | 🔴 <code>61–100 CRITICAL / FAIL</code><br>
                <em>Project-defined prototype decision thresholds, not universal semiconductor industry standards.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">
                    <span>⭕ Active Lot Wafer Overview (300mm Die Matrix)</span>
                    <span style="font-size:11px; color:#00F0FF; font-weight:600;">LOT-884A</span>
                </div>
        """, unsafe_allow_html=True)
        
        mini_defects = get_mini_wafer_defects()
        fig_mini = create_wafer_map(mini_defects, title="", is_mini=True)
        st.plotly_chart(fig_mini, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("""
            <div style="background: rgba(14, 18, 27, 0.6); padding: 12px 16px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5); font-size: 12px; margin-top: 10px;">
                <div style="color: #00F0FF; font-weight: 600; margin-bottom: 4px;">Wafer ID: W-300-9841 (Lot: LOT-884A)</div>
                <div style="color: #94A3B8; line-height: 1.5;">
                    • <strong>Spatial Pattern:</strong> Edge concentration<br>
                    • <strong>Primary Artifact:</strong> Scratch (5 occurrences)<br>
                    • <strong>Status:</strong> <span style="color:#F59E0B; font-weight:600;">HOLD FOR ENGINEER REVIEW</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 5. Recent Inspection Logs Table
    st.markdown("""
        <div class="glass-panel-card">
            <div class="panel-header-title">
                <span>📜 Recent Wafer Inspections</span>
                <span style="font-size:11px; color:#94A3B8; font-weight:400;">Live Inspection Log Stream</span>
            </div>
    """, unsafe_allow_html=True)
    
    df_recent = get_recent_inspections()
    df_display = df_recent[["Wafer ID", "Primary Defect", "Severity", "Decision", "Timestamp"]].copy()
    df_display.columns = ["Wafer ID", "Defect", "Severity", "Decision", "Time"]
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Severity": st.column_config.ProgressColumn(
                "Severity Score",
                help="Prototype score 0-100",
                format="%d",
                min_value=0,
                max_value=100
            ),
            "Decision": st.column_config.SelectboxColumn("Decision", options=["PASS", "REVIEW", "FAIL"])
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
