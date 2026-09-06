"""
SemiVision - Automated Inspection View
4-Step Inspection Workflow: Upload -> Preview -> Analyze Wafer -> AI Results Presentation
"""

import streamlit as st
from PIL import Image
import pandas as pd
import io
import time
from services.analyzer import analyze_image, generate_sample_wafer_image, generate_inspection_report_csv
from utils.visualization import create_wafer_map, create_severity_gauge

def render_inspection():
    """Renders the Inspection Workflow Interface."""
    
    st.markdown("""
        <div class="hero-header">
            <div>
                <div class="hero-title">
                    <span>🔬 Automated Wafer Surface Inspection</span>
                </div>
                <div class="hero-subtitle">Upload high-resolution wafer or chip surface macro scan for automated defect detection & severity classification</div>
            </div>
            <div class="header-status-group">
                <div class="status-badge-online">
                    <span class="status-dot-pulse"></span>
                    <span>● ENGINE ACTIVE</span>
                </div>
                <div class="badge-demo-mode">
                    <span>DEMO MODE</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # State initialization
    if "inspection_result" not in st.session_state:
        st.session_state.inspection_result = None
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    if "image_source_name" not in st.session_state:
        st.session_state.image_source_name = None

    # STEP 1: Upload Wafer/Chip Image
    st.markdown("""
        <div class="glass-panel-card">
            <div class="panel-header-title">
                <span>STEP 1: Upload Semiconductor Wafer / Chip Image</span>
                <span style="font-size:11px; color:#94A3B8;">PNG / JPG / JPEG</span>
            </div>
    """, unsafe_allow_html=True)

    col_upload, col_demo = st.columns([0.7, 0.3])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Select wafer surface macro scan image",
            type=["png", "jpg", "jpeg"],
            help="High-resolution optical microscopy or surface macro photography image."
        )

    with col_demo:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 11px; color: #94A3B8; margin-bottom: 6px;'>Need a sample scan image?</div>", unsafe_allow_html=True)
        if st.button("⚡ Load Demo Wafer Scan", type="secondary", use_container_width=True):
            img_pil, img_bytes = generate_sample_wafer_image()
            st.session_state.current_image = img_pil
            st.session_state.image_source_name = "Synthetic_300mm_Wafer_Scan.png"
            st.session_state.inspection_result = None
            st.rerun()

    if uploaded_file is not None:
        try:
            st.session_state.current_image = Image.open(uploaded_file)
            st.session_state.image_source_name = uploaded_file.name
        except Exception as e:
            st.error(f"Error reading image file: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

    # STEP 2 & STEP 3: Image Preview & Analyze Wafer Button
    if st.session_state.current_image is not None:
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">
                    <span>STEP 2 & 3: Scan Preview & Trigger AI Inspection</span>
                    <span style="font-size:11px; color:#00F0FF; font-weight:600;">IMAGE LOADED</span>
                </div>
        """, unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns([0.5, 0.5])
        with btn_col1:
            st.markdown(f"**Filename:** `{st.session_state.image_source_name}`")
            st.markdown(f"**Resolution:** `{st.session_state.current_image.size[0]} x {st.session_state.current_image.size[1]} px`")
        
        with btn_col2:
            if st.button("🚀 Analyze Wafer", type="primary", use_container_width=True):
                with st.spinner("Analyzing macro surface features & evaluating defect bounds..."):
                    time.sleep(0.5)  # Simulated processing latency
                    st.session_state.inspection_result = analyze_image(st.session_state.current_image)
                st.success("Inspection Complete!")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # STEP 4: Display Analysis Results
    res = st.session_state.inspection_result
    if res is not None:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        decision = res["decision"]
        if decision == "PASS":
            badge_class = "badge-pass"
            badge_icon = "✅"
            badge_text = "PASS — LOW SEVERITY (0-30)"
        elif decision == "REVIEW":
            badge_class = "badge-review"
            badge_icon = "⚠️"
            badge_text = "REVIEW — MEDIUM SEVERITY (31-60)"
        else:
            badge_class = "badge-fail"
            badge_icon = "🚨"
            badge_text = "FAIL — HIGH SEVERITY (61-100)"

        col_banner, col_dl = st.columns([0.7, 0.3])
        
        with col_banner:
            st.markdown(f"""
                <div class="glass-panel-card" style="padding: 16px 20px;">
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <div>
                            <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px;">Automated Decision Result</div>
                            <div style="margin-top: 4px;">
                                <span class="badge-decision {badge_class}">{badge_icon} {badge_text}</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 11px; color: #94A3B8;">Primary Defect Classification</div>
                            <div style="font-size: 18px; font-weight: 700; color: #FFFFFF;">{res['primary_defect']}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col_dl:
            st.markdown("""
                <div class="glass-panel-card" style="padding: 16px 20px; text-align: center;">
                    <div style="font-size: 11px; color: #94A3B8; margin-bottom: 6px;">Report Export</div>
            """, unsafe_allow_html=True)
            
            report_csv = generate_inspection_report_csv(res)
            st.download_button(
                label="📥 Download Inspection Report",
                data=report_csv,
                file_name=f"SemiVision_Report_{res['decision']}_{res['severity']}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

        # Original Image | AI Analysis Side-by-Side Preview
        img_col1, img_col2, gauge_col = st.columns([1, 1, 1])

        with img_col1:
            st.markdown("""
                <div class="glass-panel-card">
                    <div class="panel-header-title">Original Image</div>
            """, unsafe_allow_html=True)
            st.image(st.session_state.current_image, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with img_col2:
            st.markdown("""
                <div class="glass-panel-card">
                    <div class="panel-header-title">AI Analysis Preview</div>
            """, unsafe_allow_html=True)
            st.image(res["annotated_image"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with gauge_col:
            st.markdown("""
                <div class="glass-panel-card">
                    <div class="panel-header-title">⚡ Severity Score Gauge</div>
            """, unsafe_allow_html=True)
            
            fig_gauge = create_severity_gauge(res["severity"])
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

            st.markdown(f"""
                <div style="font-size: 12px; color: #94A3B8; line-height: 1.6; margin-top: 6px;">
                    • <strong>Defect Type:</strong> <span style="color:#00F0FF">{res['primary_defect']}</span><br>
                    • <strong>Confidence:</strong> <code>{res['confidence']*100:.1f}%</code><br>
                    • <strong>Defect Count:</strong> <code>{res['defect_count']} locations</code><br>
                    • <strong>Severity Score:</strong> <code>{res['severity']} / 100</code><br>
                    • <strong>Spatial Pattern:</strong> {res['spatial_pattern']}<br>
                </div>
                <div class="proto-disclaimer-card">
                    <strong>Prototype Decision Thresholds:</strong><br>
                    🟢 0–30 (Low/PASS) | 🟡 31–60 (Medium/REVIEW) | 🔴 61–100 (High/FAIL)<br>
                    <em>Project-defined prototype thresholds, not universal semiconductor industry standards.</em>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Defect Details Table
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">
                    <span>📋 Defect Location Details (300mm Cartesian Coordinates)</span>
                    <span style="font-size:11px; color:#94A3B8;">X/Y relative to wafer center</span>
                </div>
        """, unsafe_allow_html=True)

        if res["defects"]:
            df_det = pd.DataFrame(res["defects"])
            df_display = df_det[["id", "type", "confidence", "severity", "x", "y", "region"]].copy()
            df_display.columns = ["Defect ID", "Defect Category", "Confidence", "Severity Score", "X (mm)", "Y (mm)", "Die Region"]
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Confidence": st.column_config.NumberColumn(format="%.3f"),
                    "Severity Score": st.column_config.ProgressColumn(min_value=0, max_value=100)
                }
            )
        else:
            st.info("No surface defects detected on this wafer.")

        st.markdown("</div>", unsafe_allow_html=True)

        # 300mm Wafer Defect Map Overlay
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">⭕ 300mm Silicon Wafer Defect Spatial Visualization</div>
        """, unsafe_allow_html=True)

        fig_map = create_wafer_map(res["defects"], title="300mm Die Matrix & Defect Coordinates Overlay")
        st.plotly_chart(fig_map, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Spatial Pattern Analysis & Action Card
        st.markdown("""
            <div class="glass-panel-card">
                <div class="panel-header-title">🧠 Spatial Pattern Analysis & Action Recommendation</div>
        """, unsafe_allow_html=True)

        sp_col1, sp_col2 = st.columns([1, 1])

        with sp_col1:
            st.markdown(f"""
                <div style="background: rgba(14, 18, 27, 0.6); padding: 16px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5);">
                    <div style="color: #00F0FF; font-weight: 600; font-size: 14px; margin-bottom: 6px;">Spatial Pattern: {res['spatial_pattern']}</div>
                    <div style="font-size: 12px; color: #94A3B8; line-height: 1.5;">
                        AI spatial clustering detected pattern <strong>{res['spatial_pattern']}</strong>. 
                        Defect concentration is primarily located in the <em>{res['defects'][0]['region'] if res['defects'] else 'uniform surface'}</em>.
                    </div>
                    <div style="font-size: 11px; color: #64748B; margin-top: 10px; font-style: italic;">
                        ⚠️ Note: Spatial pattern classifications represent statistical AI clustering for process monitoring and do not prove manufacturing root cause.
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with sp_col2:
            st.markdown(f"""
                <div style="background: rgba(14, 18, 27, 0.6); padding: 16px; border-radius: 8px; border: 1px solid rgba(42, 53, 80, 0.5);">
                    <div style="color: #FFFFFF; font-weight: 600; font-size: 14px; margin-bottom: 6px;">Automated Recommendation</div>
                    <div style="font-size: 12px; color: #F8FAFC; line-height: 1.5;">
                        {res['recommendation']}
                    </div>
                    <div style="margin-top: 10px; font-size: 11px; color: #00F0FF;">
                        Summary: {res['summary']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
