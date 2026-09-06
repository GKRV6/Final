"""
SemiVision - Enhanced Visualization Utilities
Generates dark industrial Plotly charts, 300mm wafer maps, gauges, trend lines, and spatial distribution visuals.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

DARK_BG = "#0B0E14"
CARD_BG = "#121722"
GRID_COLOR = "rgba(42, 53, 80, 0.4)"
TEXT_COLOR = "#F1F5F9"
MUTED_TEXT = "#94A3B8"
CYAN_ACCENT = "#00F0FF"
BLUE_ACCENT = "#0099FF"

def create_wafer_map(defects_data, title="300mm Silicon Wafer Defect Spatial Map", is_mini=False):
    """
    Generates a dark circular wafer scatter map with semiconductor die grid matrix, notch, legend & glowing defect coordinates.
    """
    fig = go.Figure()
    
    wafer_radius = 150  # 300mm wafer diameter -> 150mm radius
    
    # 1. Add Outer Wafer Edge Circle
    theta = np.linspace(0, 2 * np.pi, 250)
    wafer_x = wafer_radius * np.cos(theta)
    wafer_y = wafer_radius * np.sin(theta)
    
    fig.add_trace(go.Scatter(
        x=wafer_x,
        y=wafer_y,
        mode='lines',
        line=dict(color=CYAN_ACCENT, width=2.5),
        hoverinfo='skip',
        showlegend=False,
        name='Wafer Edge (300mm)'
    ))

    # 2. Add Alignment Notch at Bottom (0, -150)
    notch_x = [ -8, 0, 8 ]
    notch_y = [ -148, -138, -148 ]
    fig.add_trace(go.Scatter(
        x=notch_x,
        y=notch_y,
        mode='lines',
        line=dict(color=CYAN_ACCENT, width=2.5),
        hoverinfo='skip',
        showlegend=False
    ))

    # 3. Add Semiconductor Die Matrix Grid Overlay
    grid_step = 25
    for g in range(-125, 150, grid_step):
        if abs(g) < wafer_radius:
            half_len = np.sqrt(wafer_radius**2 - g**2)
            fig.add_shape(
                type="line", x0=-half_len, y0=g, x1=half_len, y1=g,
                line=dict(color=GRID_COLOR, width=1, dash="dot")
            )
            fig.add_shape(
                type="line", x0=g, y0=-half_len, x1=g, y1=half_len,
                line=dict(color=GRID_COLOR, width=1, dash="dot")
            )

    # 4. Add Categorized Defect Scatter Points by Severity Band for Legend Support
    if defects_data:
        df_defects = pd.DataFrame(defects_data)
        
        low_sev = df_defects[df_defects['severity'] <= 30]
        med_sev = df_defects[(df_defects['severity'] > 30) & (df_defects['severity'] <= 60)]
        high_sev = df_defects[df_defects['severity'] > 60]

        marker_size = 9 if is_mini else 14

        def add_defect_trace(sub_df, name, color, symbol):
            if not sub_df.empty:
                fig.add_trace(go.Scatter(
                    x=sub_df['x'],
                    y=sub_df['y'],
                    mode='markers',
                    name=name,
                    marker=dict(
                        size=marker_size,
                        color=color,
                        line=dict(color='#FFFFFF', width=1.5),
                        symbol=symbol
                    ),
                    text=sub_df.apply(
                        lambda row: f"<b>Defect #{row['id']} - {row['type']}</b><br>"
                                    f"Severity Score: {row['severity']} / 100<br>"
                                    f"AI Confidence: {row['confidence']*100:.1f}%<br>"
                                    f"Cartesian Coordinates: ({row['x']:.1f}, {row['y']:.1f}) mm<br>"
                                    f"Die Sector: {row.get('region', 'N/A')}",
                        axis=1
                    ),
                    hoverinfo='text'
                ))

        add_defect_trace(low_sev, "Low Severity (0–30 PASS)", "#10B981", "circle")
        add_defect_trace(med_sev, "Medium Severity (31–60 REVIEW)", "#F59E0B", "diamond-wide")
        add_defect_trace(high_sev, "High Severity (61–100 CRITICAL)", "#EF4444", "hexagram")

    axis_config = dict(
        showgrid=False,
        zeroline=False,
        showticklabels=not is_mini,
        color=TEXT_COLOR,
        range=[-170, 170]
    )

    fig.update_layout(
        title=dict(
            text="" if is_mini else title,
            font=dict(color=TEXT_COLOR, size=15, family='Inter')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=axis_config,
        yaxis=dict(**axis_config, scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=30 if not is_mini else 10, b=10),
        height=330 if is_mini else 480,
        showlegend=not is_mini,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT_COLOR, size=11)
        )
    )
    return fig

def create_severity_gauge(severity_score):
    """Creates a dark industrial Plotly gauge indicator for Severity Index (0-100)."""
    if severity_score <= 30:
        bar_color = "#10B981"
        decision_label = "PASS (LOW)"
    elif severity_score <= 60:
        bar_color = "#F59E0B"
        decision_label = "REVIEW (MED)"
    else:
        bar_color = "#EF4444"
        decision_label = "CRITICAL (HIGH)"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=severity_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Severity Index<br><span style='font-size:0.85em;color:{bar_color};font-weight:700;'>{decision_label}</span>", 'font': {'size': 13, 'color': TEXT_COLOR}},
        number={'suffix': " / 100", 'font': {'size': 26, 'color': '#FFFFFF', 'family': 'JetBrains Mono'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': TEXT_COLOR, 'tickfont': {'color': TEXT_COLOR}},
            'bar': {'color': bar_color, 'thickness': 0.3},
            'bgcolor': "rgba(18, 24, 36, 0.8)",
            'borderwidth': 1,
            'bordercolor': "rgba(42, 53, 80, 0.6)",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(16, 185, 129, 0.15)'},
                {'range': [30, 60], 'color': 'rgba(245, 158, 11, 0.15)'},
                {'range': [60, 100], 'color': 'rgba(239, 68, 68, 0.15)'}
            ],
            'threshold': {
                'line': {'color': CYAN_ACCENT, 'width': 3},
                'thickness': 0.75,
                'value': severity_score
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        height=220
    )
    return fig

def create_defect_bar_chart(df_defects):
    """Generates horizontal dark bar chart of defect distribution."""
    category_col = "Defect Category" if "Defect Category" in df_defects.columns else ("Defect Type" if "Defect Type" in df_defects.columns else df_defects.columns[0])
    
    fig = px.bar(
        df_defects,
        x="Count",
        y=category_col,
        orientation="h",
        text="Count",
        color="Count",
        color_continuous_scale=[[0, "#0052CC"], [0.5, "#0099FF"], [1, "#00F0FF"]]
    )
    
    fig.update_traces(
        textposition="outside",
        marker_line_color="rgba(0,240,255,0.4)",
        marker_line_width=1
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_COLOR, title="Occurrences"),
        yaxis=dict(showgrid=False, color=TEXT_COLOR, title="", categoryorder="total ascending"),
        coloraxis_showscale=False,
        margin=dict(l=10, r=30, t=10, b=10),
        height=260,
        font=dict(color=TEXT_COLOR, family='Inter')
    )
    return fig

def create_severity_pie_chart(df_severity):
    """Generates donut chart for severity breakdown."""
    fig = go.Figure(data=[go.Pie(
        labels=df_severity['Severity Band'],
        values=df_severity['Wafer Count'],
        hole=.55,
        marker=dict(colors=df_severity['Color'], line=dict(color='#0B0E14', width=2)),
        textinfo='percent+label',
        textfont=dict(color='#FFFFFF', size=11),
        hoverinfo='label+value+percent'
    )])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=260
    )
    return fig

def create_yield_trend_chart(df_trend):
    """Generates line chart of FAB yield pass rate over time."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_trend['Date'],
        y=df_trend['Pass Rate (%)'],
        mode='lines+markers',
        name='Pass Rate (%)',
        line=dict(color='#10B981', width=3),
        marker=dict(size=6, color='#10B981')
    ))
    
    fig.add_trace(go.Scatter(
        x=df_trend['Date'],
        y=df_trend['Review Rate (%)'],
        mode='lines',
        name='Review Rate (%)',
        line=dict(color='#F59E0B', width=2, dash='dot')
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_COLOR, title="Inspection Date"),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_COLOR, title="Yield Rate (%)", range=[75, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=TEXT_COLOR)),
        margin=dict(l=10, r=10, t=30, b=10),
        height=280
    )
    return fig

def create_defects_per_wafer_hist(df_counts):
    """Generates histogram of defect occurrences per wafer."""
    fig = px.bar(
        df_counts,
        x="Defect Range",
        y="Wafer Count",
        color_discrete_sequence=[CYAN_ACCENT]
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color=TEXT_COLOR, title="Defects per Wafer"),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_COLOR, title="Wafer Count"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260
    )
    return fig

def create_spatial_pattern_bar(df_patterns):
    """Generates bar chart for spatial pattern frequencies."""
    pattern_col = "Spatial Pattern" if "Spatial Pattern" in df_patterns.columns else ("Pattern Name" if "Pattern Name" in df_patterns.columns else df_patterns.columns[0])
    
    fig = px.bar(
        df_patterns,
        x=pattern_col,
        y="Occurrences",
        color=pattern_col,
        color_discrete_sequence=["#00F0FF", "#0099FF", "#F59E0B", "#EF4444", "#10B981"]
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color=TEXT_COLOR, title="Spatial Pattern"),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, color=TEXT_COLOR, title="Wafer Occurrences"),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=260
    )
    return fig
