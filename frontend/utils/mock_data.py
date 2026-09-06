"""
SemiVision - Hackathon Demo Mock Data Service
Provides realistic semiconductor wafer inspection metrics, defect statistics, 
system operational status, historical logs, and model pipeline architecture.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_dashboard_kpis():
    """Returns top-level metric card statistics."""
    return {
        "total_inspections": {
            "value": 1482,
            "delta": "+12.4%",
            "delta_class": "positive",
            "period": "vs last week",
            "icon": "⚡"
        },
        "defects_detected": {
            "value": 143,
            "delta": "-4.2%",
            "delta_class": "positive",
            "period": "vs last week",
            "icon": "🔬"
        },
        "critical_defects": {
            "value": 18,
            "delta": "+1",
            "delta_class": "negative",
            "period": "requires engineer action",
            "icon": "🚨"
        },
        "avg_severity": {
            "value": "24.6 / 100",
            "delta": "-1.8 pts",
            "delta_class": "positive",
            "period": "prototype score",
            "icon": "🎚️"
        },
        "pass_rate": {
            "value": "90.35%",
            "delta": "+1.15%",
            "delta_class": "positive",
            "period": "0-30 severity threshold",
            "icon": "✅"
        }
    }

def get_system_status():
    """Returns real-time status for SemiVision subsystem components."""
    return {
        "AI Engine": {"status": "Demo Mode (Mock Analyzer)", "color": "#00F0FF", "badge": "ONLINE"},
        "Image Processing": {"status": "Macro Pipeline Ready", "color": "#10B981", "badge": "READY"},
        "API Service": {"status": "POST /analyze Contract Active", "color": "#10B981", "badge": "READY"},
        "Database / History": {"status": "Audit Stream Connected", "color": "#10B981", "badge": "ONLINE"}
    }

def get_defect_type_distribution():
    """Returns defect type breakdown data matching requested categories."""
    return pd.DataFrame({
        "Defect Category": ["Scratch", "Particle", "Edge-Loc", "Center", "Donut", "Random", "Other"],
        "Count": [48, 40, 22, 16, 9, 5, 3],
        "Percentage": [33.6, 28.0, 15.4, 11.2, 6.3, 3.5, 2.0]
    })

def get_severity_distribution():
    """Returns classification count by prototype severity bands."""
    return pd.DataFrame({
        "Severity Band": ["PASS (0-30)", "REVIEW (31-60)", "CRITICAL (61-100)"],
        "Wafer Count": [1339, 125, 18],
        "Percentage": [90.35, 8.43, 1.22],
        "Color": ["#10B981", "#F59E0B", "#EF4444"]
    })

def get_recent_inspections():
    """Returns recent inspection logs DataFrame."""
    now = datetime.now()
    data = [
        {"Inspection ID": "INS-90481", "Wafer ID": "W-300-9841", "Lot ID": "LOT-884A", "Timestamp": (now - timedelta(minutes=14)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "Scratch", "Defect Count": 5, "Severity": 78, "Decision": "REVIEW", "Confidence": 0.968, "Spatial Pattern": "Edge concentration"},
        {"Inspection ID": "INS-90480", "Wafer ID": "W-300-9840", "Lot ID": "LOT-884A", "Timestamp": (now - timedelta(minutes=32)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "None (Clean)", "Defect Count": 0, "Severity": 4, "Decision": "PASS", "Confidence": 0.992, "Spatial Pattern": "Random distribution"},
        {"Inspection ID": "INS-90479", "Wafer ID": "W-300-9839", "Lot ID": "LOT-884A", "Timestamp": (now - timedelta(minutes=48)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "Particle", "Defect Count": 12, "Severity": 84, "Decision": "FAIL", "Confidence": 0.954, "Spatial Pattern": "Clustered defects"},
        {"Inspection ID": "INS-90478", "Wafer ID": "W-300-9838", "Lot ID": "LOT-883F", "Timestamp": (now - timedelta(hours=1, minutes=15)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "Center", "Defect Count": 3, "Severity": 42, "Decision": "REVIEW", "Confidence": 0.941, "Spatial Pattern": "Center concentration"},
        {"Inspection ID": "INS-90477", "Wafer ID": "W-300-9837", "Lot ID": "LOT-883F", "Timestamp": (now - timedelta(hours=1, minutes=40)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "Donut", "Defect Count": 1, "Severity": 18, "Decision": "PASS", "Confidence": 0.975, "Spatial Pattern": "Periodic pattern"},
        {"Inspection ID": "INS-90476", "Wafer ID": "W-300-9836", "Lot ID": "LOT-883F", "Timestamp": (now - timedelta(hours=2, minutes=5)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "Scratch", "Defect Count": 2, "Severity": 28, "Decision": "PASS", "Confidence": 0.938, "Spatial Pattern": "Edge concentration"},
        {"Inspection ID": "INS-90475", "Wafer ID": "W-300-9835", "Lot ID": "LOT-882C", "Timestamp": (now - timedelta(hours=2, minutes=50)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "Edge-Loc", "Defect Count": 4, "Severity": 92, "Decision": "FAIL", "Confidence": 0.988, "Spatial Pattern": "Edge concentration"},
        {"Inspection ID": "INS-90474", "Wafer ID": "W-300-9834", "Lot ID": "LOT-882C", "Timestamp": (now - timedelta(hours=3, minutes=10)).strftime("%Y-%m-%d %H:%M"), "Primary Defect": "None (Clean)", "Defect Count": 0, "Severity": 2, "Decision": "PASS", "Confidence": 0.995, "Spatial Pattern": "Random distribution"}
    ]
    return pd.DataFrame(data)

def get_mini_wafer_defects():
    """Returns sample defect coordinates for Dashboard mini wafer plot."""
    return [
        {"id": 1, "x": 120.5, "y": 45.2, "type": "Scratch", "confidence": 0.96, "severity": 78, "region": "Periphery"},
        {"id": 2, "x": 115.0, "y": 55.8, "type": "Scratch", "confidence": 0.94, "severity": 72, "region": "Periphery"},
        {"id": 3, "x": 128.2, "y": 30.1, "type": "Particle", "confidence": 0.89, "severity": 54, "region": "Periphery"},
        {"id": 4, "x": -15.4, "y": 8.2, "type": "Center", "confidence": 0.91, "severity": 22, "region": "Center"},
        {"id": 5, "x": -135.0, "y": -20.5, "type": "Edge-Loc", "confidence": 0.88, "severity": 65, "region": "Edge Notch"}
    ]

def get_yield_trend_data():
    """Returns 14-day FAB yield trend data."""
    dates = [(datetime.now() - timedelta(days=i)).strftime("%b %d") for i in range(13, -1, -1)]
    pass_rates = [88.2, 89.0, 88.5, 90.1, 91.2, 89.8, 90.5, 91.0, 90.8, 92.1, 91.5, 89.9, 90.2, 90.35]
    review_rates = [9.5, 9.1, 9.8, 8.2, 7.5, 8.4, 7.8, 7.5, 7.9, 6.8, 7.2, 8.6, 8.3, 8.43]
    return pd.DataFrame({
        "Date": dates,
        "Pass Rate (%)": pass_rates,
        "Review Rate (%)": review_rates
    })

def get_defects_per_wafer_data():
    """Returns histogram distribution data for defects per wafer."""
    return pd.DataFrame({
        "Defect Range": ["0 (Clean)", "1-2 Defects", "3-5 Defects", "6-10 Defects", ">10 Defects"],
        "Wafer Count": [1080, 259, 110, 22, 11]
    })

def get_spatial_pattern_data():
    """Returns spatial pattern frequency distribution."""
    return pd.DataFrame({
        "Spatial Pattern": ["Edge concentration", "Random distribution", "Center concentration", "Clustered defects", "Periodic pattern"],
        "Occurrences": [64, 45, 22, 12, 6]
    })

def get_model_pipeline_info():
    """Returns model pipeline details with explicit pending integration status."""
    return {
        "pipeline_stages": [
            {"step": 1, "name": "Image Preprocessing", "status": "Ready", "tech": "OpenCV / Pillow Normalization & Macro Calibration"},
            {"step": 2, "name": "Defect Detection", "status": "Integration Pending", "tech": "YOLO-based Detector"},
            {"step": 3, "name": "Defect Segmentation", "status": "Integration Pending", "tech": "SAM / U-Net-based Segmentation"},
            {"step": 4, "name": "Defect Classification", "status": "Integration Pending", "tech": "CNN / ViT Classifier"},
            {"step": 5, "name": "Anomaly Detection", "status": "Integration Pending", "tech": "PatchCore / Autoencoder-based Engine"},
            {"step": 6, "name": "Severity Analysis", "status": "Ready (Prototype Thresholds)", "tech": "Rule-based Prototype Scoring Index"},
            {"step": 7, "name": "Wafer Spatial Mapping", "status": "Ready", "tech": "Polar & 300mm Die Matrix Cartesian Mapping"}
        ],
        "supported_categories": ["Scratch", "Particle", "Edge-Loc", "Center", "Donut", "Random", "Other"],
        "metrics_notice": "Model evaluation metrics (mAP, Precision, Recall, F1) will be populated after formal model training and validation on FAB dataset.",
        "api_endpoint": "http://localhost:8000/api/v1/analyze"
    }
