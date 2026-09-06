"""
SemiVision - AI Inspection Service (Mock API-Ready Implementation)

Decoupled mock analysis logic. 
This module simulates semiconductor defect detection, classification, 
spatial pattern analysis, severity scoring, and downloadable report generation.

Later, `analyze_image(image)` can be replaced with a REST API call (e.g. `POST /analyze`)
without modifying the UI components.
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import io
import pandas as pd

DEFECT_TYPES = [
    "Scratch", 
    "Micro-Particle", 
    "Pattern Shift", 
    "Contamination", 
    "Die Crack", 
    "Bridging"
]

SPATIAL_PATTERNS = [
    "Edge Concentration", 
    "Center Concentration", 
    "Clustered Defects", 
    "Random Distribution"
]

RECOMMENDATIONS = {
    "PASS": "Wafer passed all inspection criteria. Clear for next fabrication process step.",
    "REVIEW": "Hold wafer for engineer review. Recommend CMP & optical re-inspection of flagged die regions.",
    "FAIL": "CRITICAL ALARM: Quarantine wafer lot immediately. Initiate etch chamber diagnostic & particle audit."
}

def analyze_image(image_input, preset_severity=None):
    """
    Simulates AI semiconductor defect inspection on an uploaded wafer image.
    
    Parameters:
        image_input: PIL.Image object or BytesIO stream
        preset_severity: Optional severity override for deterministic testing
        
    Returns:
        Structured inspection result dict (API ready)
    """
    if isinstance(image_input, Image.Image):
        orig_img = image_input.convert("RGB")
    else:
        orig_img = Image.open(image_input).convert("RGB")
        
    img_w, img_h = orig_img.size
    
    if preset_severity is not None:
        severity_score = int(preset_severity)
    else:
        severity_score = random.choice([22, 28, 48, 55, 78, 86, 92])
        
    # Prototype Decision Threshold Logic
    # 0-30 = LOW / PASS
    # 31-60 = MEDIUM / REVIEW
    # 61-100 = HIGH / CRITICAL (FAIL)
    if severity_score <= 30:
        decision = "PASS"
        defect_count = random.randint(0, 2)
        primary_defect = "None (Minor Particle)" if defect_count > 0 else "None (Clean)"
        spatial_pattern = "Random Distribution" if defect_count > 0 else "Uniform / Clean"
    elif severity_score <= 60:
        decision = "REVIEW"
        defect_count = random.randint(3, 6)
        primary_defect = random.choice(["Scratch", "Pattern Shift", "Contamination"])
        spatial_pattern = random.choice(["Edge Concentration", "Center Concentration"])
    else:
        decision = "FAIL"
        defect_count = random.randint(7, 14)
        primary_defect = random.choice(["Scratch", "Die Crack", "Micro-Particle"])
        spatial_pattern = random.choice(["Edge Concentration", "Clustered Defects"])

    defects = []
    annotated_img = orig_img.copy()
    draw = ImageDraw.Draw(annotated_img)
    
    try:
        font = ImageFont.truetype("arial.ttf", max(12, int(img_w * 0.025)))
    except IOError:
        font = ImageFont.load_default()

    center_x, center_y = img_w / 2, img_h / 2
    pixel_to_mm = 300.0 / min(img_w, img_h)

    for i in range(1, defect_count + 1):
        def_type = primary_defect if i <= max(1, defect_count // 2) else random.choice(DEFECT_TYPES)
        conf = round(random.uniform(0.85, 0.99), 3)
        def_sev = max(10, min(100, int(severity_score + random.randint(-15, 10))))
        
        if spatial_pattern == "Edge Concentration":
            angle = random.uniform(0, 2 * np.pi)
            r = random.uniform(img_w * 0.35, img_w * 0.45)
            px = center_x + r * np.cos(angle)
            py = center_y + r * np.sin(angle)
            region = "Periphery"
        elif spatial_pattern == "Center Concentration":
            angle = random.uniform(0, 2 * np.pi)
            r = random.uniform(0, img_w * 0.18)
            px = center_x + r * np.cos(angle)
            py = center_y + r * np.sin(angle)
            region = "Center Die"
        elif spatial_pattern == "Clustered Defects":
            base_angle = 0.75 * np.pi
            r = random.uniform(img_w * 0.2, img_w * 0.3)
            px = center_x + r * np.cos(base_angle) + random.uniform(-20, 20)
            py = center_y + r * np.sin(base_angle) + random.uniform(-20, 20)
            region = "Die Sector 4"
        else:
            px = random.uniform(img_w * 0.15, img_w * 0.85)
            py = random.uniform(img_h * 0.15, img_h * 0.85)
            region = "Random Die"

        mm_x = round((px - center_x) * pixel_to_mm, 1)
        mm_y = round((center_y - py) * pixel_to_mm, 1)

        box_size = max(24, int(img_w * 0.04))
        x0, y0 = max(0, px - box_size), max(0, py - box_size)
        x1, y1 = min(img_w, px + box_size), min(img_h, py + box_size)

        box_color = "#10B981" if def_sev <= 30 else ("#F59E0B" if def_sev <= 60 else "#EF4444")
        
        draw.rectangle([x0, y0, x1, y1], outline=box_color, width=3)
        draw.line([px - 6, py, px + 6, py], fill=box_color, width=2)
        draw.line([px, py - 6, px, py + 6], fill=box_color, width=2)
        label_str = f"#{i} {def_type} ({int(conf*100)}%)"
        draw.text((x0, max(0, y0 - 16)), label_str, fill=box_color, font=font)

        defects.append({
            "id": i,
            "x": mm_x,
            "y": mm_y,
            "type": def_type,
            "confidence": conf,
            "severity": def_sev,
            "region": region,
            "bbox": [int(x0), int(y0), int(x1), int(y1)]
        })

    recommendation = RECOMMENDATIONS.get(decision, "Review wafer with process engineering team.")
    
    summary = (
        f"Mock AI analysis identified {defect_count} defect location(s) with primary pattern '{primary_defect}'. "
        f"Prototype severity index scored {severity_score}/100, resulting in a '{decision}' decision."
    )

    return {
        "primary_defect": primary_defect,
        "confidence": round(random.uniform(0.92, 0.98), 3),
        "defect_count": defect_count,
        "severity": severity_score,
        "decision": decision,
        "spatial_pattern": spatial_pattern,
        "recommendation": recommendation,
        "summary": summary,
        "defects": defects,
        "annotated_image": annotated_img
    }

def generate_sample_wafer_image():
    """Generates a realistic dark synthetic silicon wafer image with die matrix for quick testing."""
    size = (600, 600)
    img = Image.new("RGB", size, color=(11, 14, 20))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = 300, 300
    radius = 270
    
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=(22, 28, 42),
        outline=(0, 240, 255),
        width=3
    )
    
    draw.polygon([(292, 570), (300, 555), (308, 570)], fill=(11, 14, 20), outline=(0, 240, 255))
    
    die_step = 30
    for x in range(30, 570, die_step):
        for y in range(30, 570, die_step):
            if (x - center_x)**2 + (y - center_y)**2 < (radius - 10)**2:
                draw.rectangle([x, y, x + die_step - 2, y + die_step - 2], fill=(28, 36, 52), outline=(42, 50, 75))
                
    draw.line([(380, 180), (450, 230), (490, 280)], fill=(200, 220, 240), width=2)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return img, buf

def generate_inspection_report_csv(result):
    """Generates a CSV string representation of the inspection results."""
    meta = [{
        "Primary Defect": result["primary_defect"],
        "Decision": result["decision"],
        "Severity Score": result["severity"],
        "AI Confidence": result["confidence"],
        "Defect Count": result["defect_count"],
        "Spatial Pattern": result["spatial_pattern"],
        "Recommendation": result["recommendation"]
    }]
    df_meta = pd.DataFrame(meta)
    df_defects = pd.DataFrame(result["defects"]) if result["defects"] else pd.DataFrame()
    
    csv_buf = io.StringIO()
    csv_buf.write("--- SEMIVISION AUTOMATED INSPECTION SUMMARY REPORT ---\n")
    df_meta.to_csv(csv_buf, index=False)
    csv_buf.write("\n--- DETECTED DEFECT LOCATIONS (300mm CARTESIAN COORD) ---\n")
    df_defects.to_csv(csv_buf, index=False)
    return csv_buf.getvalue().encode('utf-8')
