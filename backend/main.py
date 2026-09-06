from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from PIL import Image

import torch
from torchvision import models, transforms

import io
import os
import json
from datetime import datetime

import numpy as np
import matplotlib.cm as cm


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="SemiVision - Semiconductor Wafer Defect Detection API",
    description="AI-based semiconductor wafer defect detection using ResNet50",
    version="1.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DEFECT CLASSES
# =========================================================

classes = [
    "Center",
    "Donut",
    "Edge-Loc",
    "Edge-Ring",
    "Loc",
    "Near-full",
    "Random",
    "Scratch"
]


# =========================================================
# DEVICE
# =========================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# =========================================================
# PATHS
# =========================================================

# Project root
project_root = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# Model path
model_path = os.path.join(
    project_root,
    "models",
    "resnet50_wafer.pth"
)


# Heatmap folder
heatmap_folder = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "heatmaps"
)


# History file
history_file = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "inspection_history.json"
)


# =========================================================
# CREATE REQUIRED FOLDERS / FILES
# =========================================================

os.makedirs(
    heatmap_folder,
    exist_ok=True
)


if not os.path.exists(history_file):

    with open(history_file, "w") as f:
        json.dump([], f, indent=4)


# =========================================================
# RESNET50 MODEL
# =========================================================

model = models.resnet50(
    weights=None
)


# Replace final classification layer
model.fc = torch.nn.Linear(
    model.fc.in_features,
    8
)


# =========================================================
# LOAD TRAINED MODEL
# =========================================================

if not os.path.exists(model_path):

    raise FileNotFoundError(
        f"Model file not found: {model_path}"
    )


model.load_state_dict(
    torch.load(
        model_path,
        map_location=device
    )
)


model = model.to(device)

model.eval()

print("ResNet50 model loaded successfully")


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

transform = transforms.Compose([

    transforms.Grayscale(
        num_output_channels=3
    ),

    transforms.Resize(
        (224, 224)
    ),

    transforms.ToTensor()
])


# =========================================================
# HEATMAP STATIC FILES
# =========================================================

app.mount(
    "/heatmaps",
    StaticFiles(
        directory=heatmap_folder
    ),
    name="heatmaps"
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Semiconductor Wafer Defect Detection API is running",
        "model": "ResNet50",
        "device": str(device),
        "classes": classes
    }


# =========================================================
# PREDICT
# =========================================================

@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # Read uploaded image
    # -----------------------------------------------------

    image_data = await file.read()

    original_image = Image.open(
        io.BytesIO(image_data)
    ).convert("RGB")


    # -----------------------------------------------------
    # Preprocess image
    # -----------------------------------------------------

    image_tensor = transform(
        original_image
    )

    image_tensor = image_tensor.unsqueeze(0)

    image_tensor = image_tensor.to(device)


    # -----------------------------------------------------
    # Grad-CAM storage
    # -----------------------------------------------------

    activations = []
    gradients = []


    # -----------------------------------------------------
    # Forward hook
    # -----------------------------------------------------

    def forward_hook(
        module,
        input,
        output
    ):

        activations.append(
            output
        )


    # -----------------------------------------------------
    # Backward hook
    # -----------------------------------------------------

    def backward_hook(
        module,
        grad_input,
        grad_output
    ):

        gradients.append(
            grad_output[0]
        )


    # -----------------------------------------------------
    # Grad-CAM target layer
    # -----------------------------------------------------

    target_layer = model.layer4[-1]


    forward_handle = target_layer.register_forward_hook(
        forward_hook
    )


    backward_handle = target_layer.register_full_backward_hook(
        backward_hook
    )


    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    model.zero_grad()

    outputs = model(
        image_tensor
    )


    # -----------------------------------------------------
    # Probabilities
    # -----------------------------------------------------

    probabilities = torch.softmax(
        outputs,
        dim=1
    )


    # -----------------------------------------------------
    # Highest probability class
    # -----------------------------------------------------

    confidence, predicted = torch.max(
        probabilities,
        1
    )


    # -----------------------------------------------------
    # Backpropagate predicted class
    # -----------------------------------------------------

    score = outputs[
        0,
        predicted.item()
    ]

    score.backward()


    # -----------------------------------------------------
    # Remove hooks
    # -----------------------------------------------------

    forward_handle.remove()

    backward_handle.remove()


    # -----------------------------------------------------
    # Get Grad-CAM data
    # -----------------------------------------------------

    activation = activations[0]

    gradient = gradients[0]


    # -----------------------------------------------------
    # Calculate Grad-CAM weights
    # -----------------------------------------------------

    weights = gradient.mean(
        dim=(2, 3),
        keepdim=True
    )


    # -----------------------------------------------------
    # Generate CAM
    # -----------------------------------------------------

    cam = (
        weights * activation
    ).sum(
        dim=1
    )


    # -----------------------------------------------------
    # Remove negative values
    # -----------------------------------------------------

    cam = torch.relu(
        cam
    )


    # -----------------------------------------------------
    # Normalize CAM
    # -----------------------------------------------------

    cam = cam[
        0
    ].detach().cpu().numpy()


    cam = cam - cam.min()


    if cam.max() != 0:

        cam = cam / cam.max()


    # -----------------------------------------------------
    # Convert CAM to heatmap
    # -----------------------------------------------------

    heatmap = cm.jet(
        cam
    )[:, :, :3]


    heatmap = np.uint8(
        heatmap * 255
    )


    heatmap_image = Image.fromarray(
        heatmap
    )


    # -----------------------------------------------------
    # Resize heatmap
    # -----------------------------------------------------

    heatmap_image = heatmap_image.resize(
        original_image.size
    )


    # -----------------------------------------------------
    # Create overlay
    # -----------------------------------------------------

    overlay = Image.blend(
        original_image,
        heatmap_image,
        alpha=0.5
    )


    # -----------------------------------------------------
    # Unique heatmap filename
    # -----------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


    heatmap_filename = (
        f"heatmap_{timestamp}.png"
    )


    heatmap_path = os.path.join(
        heatmap_folder,
        heatmap_filename
    )


    # -----------------------------------------------------
    # Save heatmap
    # -----------------------------------------------------

    overlay.save(
        heatmap_path
    )


    # -----------------------------------------------------
    # Final prediction values
    # -----------------------------------------------------

    defect = classes[
        predicted.item()
    ]


    confidence_percentage = (
        confidence.item() * 100
    )


    # =====================================================
    # SAVE INSPECTION HISTORY
    # =====================================================

    try:

        with open(
            history_file,
            "r"
        ) as f:

            history = json.load(f)

    except:

        history = []


    # -----------------------------------------------------
    # Create inspection record
    # -----------------------------------------------------

    record = {

        "id": len(history) + 1,

        "wafer_id": file.filename,

        "defect": defect,

        "confidence": round(
            confidence_percentage,
            2
        ),

        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "heatmap": (
            f"/heatmaps/{heatmap_filename}"
        )
    }


    # -----------------------------------------------------
    # Add record
    # -----------------------------------------------------

    history.append(
        record
    )


    # -----------------------------------------------------
    # Save history
    # -----------------------------------------------------

    with open(
        history_file,
        "w"
    ) as f:

        json.dump(
            history,
            f,
            indent=4
        )


    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {

        "defect": defect,

        "confidence": round(
            confidence_percentage,
            2
        ),

        "heatmap": (
            f"/heatmaps/{heatmap_filename}"
        ),

        "wafer_id": file.filename,

        "timestamp": record["timestamp"]
    }


# =========================================================
# INSPECTION HISTORY
# =========================================================

@app.get("/history")
def get_history():

    try:

        with open(
            history_file,
            "r"
        ) as f:

            history = json.load(f)

    except:

        history = []


    return {
        "total_inspections": len(history),
        "inspections": history
    }


# =========================================================
# CLEAR HISTORY
# =========================================================

@app.delete("/history")
def clear_history():

    with open(
        history_file,
        "w"
    ) as f:

        json.dump(
            [],
            f,
            indent=4
        )


    return {
        "message": "Inspection history cleared successfully"
    }