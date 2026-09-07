from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from PIL import Image, ImageFilter

import torch
from torchvision import models, transforms

import io
import os
import json
from datetime import datetime

import numpy as np
import matplotlib.cm as cm


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="SemiVision - Semiconductor Wafer Defect Detection API",
    description="AI-based semiconductor wafer defect detection using ResNet50",
    version="1.3"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DEFECT CLASSES
# ============================================================

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


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)

if torch.cuda.is_available():
    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )


# ============================================================
# PROJECT PATHS
# ============================================================

project_root = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

models_dir = os.path.join(
    project_root,
    "models"
)

resnet50_path = os.path.join(
    models_dir,
    "resnet50_wafer.pth"
)

resnet18_path = os.path.join(
    models_dir,
    "resnet18_wafer_best.pth"
)

efficientnet_b2_path = os.path.join(
    models_dir,
    "efficientnet_b2_best.pth"
)

backend_folder = os.path.dirname(
    os.path.abspath(__file__)
)

heatmap_folder = os.path.join(
    backend_folder,
    "heatmaps"
)

history_file = os.path.join(
    backend_folder,
    "inspection_history.json"
)


# ============================================================
# CREATE REQUIRED FOLDERS / FILES
# ============================================================

os.makedirs(
    heatmap_folder,
    exist_ok=True
)

if not os.path.exists(history_file):

    with open(
        history_file,
        "w"
    ) as f:

        json.dump(
            [],
            f,
            indent=4
        )


# ============================================================
# LOAD 3-MODEL ENSEMBLE (ResNet50, ResNet18, EfficientNet-B2)
# ============================================================

num_classes = len(classes)

# 1. ResNet50
if not os.path.exists(resnet50_path):
    raise FileNotFoundError(f"ResNet50 model file not found: {resnet50_path}")

model_resnet50 = models.resnet50(weights=None)
model_resnet50.fc = torch.nn.Linear(
    model_resnet50.fc.in_features,
    num_classes
)
model_resnet50.load_state_dict(
    torch.load(
        resnet50_path,
        map_location=device
    )
)
model_resnet50 = model_resnet50.to(device)
model_resnet50.eval()
print("ResNet50 model loaded successfully")

# 2. ResNet18
if not os.path.exists(resnet18_path):
    raise FileNotFoundError(f"ResNet18 model file not found: {resnet18_path}")

model_resnet18 = models.resnet18(weights=None)
model_resnet18.fc = torch.nn.Linear(
    model_resnet18.fc.in_features,
    num_classes
)
r18_checkpoint = torch.load(
    resnet18_path,
    map_location=device
)
r18_state_dict = (
    r18_checkpoint["model_state_dict"]
    if isinstance(r18_checkpoint, dict) and "model_state_dict" in r18_checkpoint
    else r18_checkpoint
)
model_resnet18.load_state_dict(r18_state_dict)
model_resnet18 = model_resnet18.to(device)
model_resnet18.eval()
print("ResNet18 model loaded successfully")

# 3. EfficientNet-B2
if not os.path.exists(efficientnet_b2_path):
    raise FileNotFoundError(f"EfficientNet-B2 model file not found: {efficientnet_b2_path}")

model_efficientnet_b2 = models.efficientnet_b2(weights=None)
model_efficientnet_b2.classifier[1] = torch.nn.Linear(
    model_efficientnet_b2.classifier[1].in_features,
    num_classes
)
eff_checkpoint = torch.load(
    efficientnet_b2_path,
    map_location=device
)
eff_state_dict = (
    eff_checkpoint["model_state_dict"]
    if isinstance(eff_checkpoint, dict) and "model_state_dict" in eff_checkpoint
    else eff_checkpoint
)
model_efficientnet_b2.load_state_dict(eff_state_dict)
model_efficientnet_b2 = model_efficientnet_b2.to(device)
model_efficientnet_b2.eval()
print("EfficientNet-B2 model loaded successfully")

# Keep alias for Grad-CAM compatibility
model = model_resnet50


# ============================================================
# IMAGE PREPROCESSING TRANSFORMS
# ============================================================

# ResNets (224 x 224)
transform_224 = transforms.Compose([
    transforms.Grayscale(
        num_output_channels=3
    ),

    transforms.Resize(
        (224, 224)
    ),

    transforms.ToTensor()
])

# EfficientNet-B2 (260 x 260)
transform_260 = transforms.Compose([
    transforms.Grayscale(
        num_output_channels=3
    ),

    transforms.Resize(
        (260, 260)
    ),

    transforms.ToTensor()
])

transform = transform_224


# ============================================================
# SERVE HEATMAP IMAGES
# ============================================================

app.mount(
    "/heatmaps",
    StaticFiles(
        directory=heatmap_folder
    ),
    name="heatmaps"
)


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.get("/")
def home():

    return {

        "message":
            "Semiconductor Wafer Defect Detection API is running",

        "model":
            "Ensemble (ResNet50 + EfficientNet-B2 + ResNet18)",

        "device":
            str(device),

        "classes":
            classes
    }


# ============================================================
# CREATE WAFER MASK
# ============================================================

def create_wafer_mask(image):
    """
    Creates an approximate mask of the actual wafer.

    The WM-811K wafer maps have a bright wafer region
    surrounded by a dark/black background.

    This mask prevents Grad-CAM activation outside
    the actual wafer from appearing in the heatmap.
    """

    # --------------------------------------------------------
    # Convert image to grayscale
    # --------------------------------------------------------

    gray = image.convert(
        "L"
    )

    # --------------------------------------------------------
    # Resize to the same resolution used by ResNet50
    # --------------------------------------------------------

    gray = gray.resize(
        (224, 224),
        Image.Resampling.BILINEAR
    )

    gray_array = np.array(
        gray
    )

    # --------------------------------------------------------
    # Detect wafer pixels
    #
    # Pixels brighter than a small threshold are treated
    # as part of the wafer.
    # --------------------------------------------------------

    threshold = 10

    mask_array = (
        gray_array > threshold
    ).astype(
        np.uint8
    ) * 255

    mask_image = Image.fromarray(
        mask_array
    )

    # --------------------------------------------------------
    # Slightly close small holes in the wafer mask.
    #
    # This helps prevent dark defect pixels inside the wafer
    # from creating holes in the mask.
    # --------------------------------------------------------

    mask_image = mask_image.filter(
        ImageFilter.MaxFilter(5)
    )

    mask_image = mask_image.filter(
        ImageFilter.MinFilter(5)
    )

    mask_array = np.array(
        mask_image
    ) > 0

    # --------------------------------------------------------
    # Safety fallback
    #
    # If a valid wafer cannot be detected, use the whole
    # image so prediction still works.
    # --------------------------------------------------------

    if np.sum(mask_array) < 100:

        mask_array = np.ones(
            (224, 224),
            dtype=bool
        )

    return mask_array


# ============================================================
# GRAD-CAM LOCALIZATION
# ============================================================

def get_defect_location(
    cam,
    wafer_mask
):

    """
    Calculates approximate defect location and
    high-activation region using Grad-CAM.

    IMPORTANT:
    This is coarse AI-assisted localization.
    It is NOT true pixel-level segmentation.
    """

    # --------------------------------------------------------
    # Ensure positive CAM
    # --------------------------------------------------------

    cam = np.maximum(
        cam,
        0
    )


    # --------------------------------------------------------
    # Normalize CAM between 0 and 1
    # --------------------------------------------------------

    if cam.max() > 0:

        cam = (
            cam
            /
            cam.max()
        )


    # --------------------------------------------------------
    # Upscale CAM to 224 x 224
    #
    # ResNet50 layer4 produces a small feature map.
    # Upscaling gives a much more granular area calculation.
    # --------------------------------------------------------

    cam_image = Image.fromarray(
        cam.astype(np.float32),
        mode="F"
    )

    cam_image = cam_image.resize(
        (224, 224),
        Image.Resampling.BILINEAR
    )

    cam = np.array(
        cam_image
    )


    # --------------------------------------------------------
    # Normalize again after interpolation
    # --------------------------------------------------------

    cam = cam - cam.min()

    if cam.max() > 0:

        cam = (
            cam
            /
            cam.max()
        )


    # --------------------------------------------------------
    # IMPORTANT:
    # Remove Grad-CAM activation outside the wafer.
    # --------------------------------------------------------

    cam = np.where(
        wafer_mask,
        cam,
        0
    )


    height, width = cam.shape


    # --------------------------------------------------------
    # Strong activation threshold
    # --------------------------------------------------------

    threshold = 0.60

    mask = (
        cam >= threshold
    )

    # Only consider pixels inside wafer
    mask = (
        mask
        &
        wafer_mask
    )


    # --------------------------------------------------------
    # Fallback for very small activation regions
    # --------------------------------------------------------

    if np.sum(mask) < 20:

        threshold = 0.45

        mask = (
            cam >= threshold
        )

        mask = (
            mask
            &
            wafer_mask
        )


    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    if np.sum(mask) == 0:

        wafer_values = np.where(
            wafer_mask,
            cam,
            -1
        )

        max_y, max_x = np.unravel_index(
            np.argmax(
                wafer_values
            ),
            cam.shape
        )

        mask = np.zeros_like(
            cam,
            dtype=bool
        )

        mask[
            max_y,
            max_x
        ] = True


    # ========================================================
    # WEIGHTED ACTIVATION CENTER
    # ========================================================

    total_activation = cam.sum()

    if total_activation > 0:

        y_indices, x_indices = np.indices(
            cam.shape
        )

        center_x = (
            (x_indices * cam).sum()
            /
            total_activation
        )

        center_y = (
            (y_indices * cam).sum()
            /
            total_activation
        )

    else:

        center_x = width / 2

        center_y = height / 2


    # ========================================================
    # HORIZONTAL LOCATION
    # ========================================================

    if center_x < width * 0.33:

        horizontal = "Left"

    elif center_x > width * 0.67:

        horizontal = "Right"

    else:

        horizontal = "Center"


    # ========================================================
    # VERTICAL LOCATION
    # ========================================================

    if center_y < height * 0.33:

        vertical = "Upper"

    elif center_y > height * 0.67:

        vertical = "Lower"

    else:

        vertical = "Middle"


    # ========================================================
    # COMBINE LOCATION
    # ========================================================

    if (
        horizontal == "Center"
        and
        vertical == "Middle"
    ):

        location = "Center"

    elif horizontal == "Center":

        location = vertical

    elif vertical == "Middle":

        location = horizontal

    else:

        location = (
            f"{vertical} {horizontal}"
        )


    # ========================================================
    # HIGH-ACTIVATION REGION
    #
    # IMPORTANT:
    # Calculate the percentage ONLY inside the wafer.
    #
    # This prevents background pixels from affecting
    # the activation-area calculation.
    # ========================================================

    activated_pixels = np.sum(
        mask
    )

    wafer_pixels = np.sum(
        wafer_mask
    )

    if wafer_pixels > 0:

        activation_percentage = (
            activated_pixels
            /
            wafer_pixels
        ) * 100

    else:

        activation_percentage = 0


    # ========================================================
    # RETURN LOCALIZATION INFORMATION
    # ========================================================

    return {

        "location":
            location,

        "affected_area":
            round(
                float(
                    activation_percentage
                ),
                2
            ),

        "threshold":
            threshold
    }


# ============================================================
# PREDICTION ENDPOINT
# ============================================================

@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):

    # ========================================================
    # READ IMAGE
    # ========================================================

    image_data = await file.read()

    original_image = Image.open(
        io.BytesIO(
            image_data
        )
    ).convert(
        "RGB"
    )


    # ========================================================
    # PREPROCESS IMAGE (224x224 FOR RESNETS, 260x260 FOR EFFNET)
    # ========================================================

    image_tensor_224 = transform_224(
        original_image
    ).unsqueeze(
        0
    ).to(
        device
    )

    image_tensor_260 = transform_260(
        original_image
    ).unsqueeze(
        0
    ).to(
        device
    )

    image_tensor = image_tensor_224


    # ========================================================
    # CREATE WAFER MASK
    # ========================================================

    wafer_mask = create_wafer_mask(
        original_image
    )


    # ========================================================
    # GRAD-CAM STORAGE
    # ========================================================

    activations = []

    gradients = []


    # ========================================================
    # FORWARD HOOK
    # ========================================================

    def forward_hook(
        module,
        input,
        output
    ):

        activations.append(
            output
        )


    # ========================================================
    # BACKWARD HOOK
    # ========================================================

    def backward_hook(
        module,
        grad_input,
        grad_output
    ):

        gradients.append(
            grad_output[0]
        )


    # ========================================================
    # TARGET LAYER (GRAD-CAM ON RESNET50)
    # ========================================================

    target_layer = model_resnet50.layer4[-1]


    forward_handle = (
        target_layer.register_forward_hook(
            forward_hook
        )
    )

    backward_handle = (
        target_layer.register_full_backward_hook(
            backward_hook
        )
    )


    # ========================================================
    # FORWARD PASS: RESNET50 (WITH GRAD-CAM HOOKS)
    # ========================================================

    model_resnet50.zero_grad()

    outputs_resnet50 = model_resnet50(
        image_tensor_224
    )

    probs_resnet50 = torch.softmax(
        outputs_resnet50,
        dim=1
    )


    # ========================================================
    # FORWARD PASS: RESNET18 & EFFICIENTNET-B2
    # ========================================================

    with torch.no_grad():

        outputs_resnet18 = model_resnet18(
            image_tensor_224
        )

        probs_resnet18 = torch.softmax(
            outputs_resnet18,
            dim=1
        )

        outputs_eff = model_efficientnet_b2(
            image_tensor_260
        )

        probs_eff = torch.softmax(
            outputs_eff,
            dim=1
        )


    # ========================================================
    # WEIGHTED SOFT-VOTING ENSEMBLE
    # 0.40 * ResNet50 + 0.40 * EfficientNet-B2 + 0.20 * ResNet18
    # ========================================================

    ensemble_probs = (
        0.40 * probs_resnet50
        + 0.40 * probs_eff
        + 0.20 * probs_resnet18
    )

    confidence, predicted = torch.max(
        ensemble_probs,
        1
    )

    # --------------------------------------------------------
    # INDIVIDUAL MODEL PREDICTIONS FOR ENSEMBLE BREAKDOWN
    # --------------------------------------------------------

    conf_r50, pred_r50 = torch.max(probs_resnet50, 1)
    conf_r18, pred_r18 = torch.max(probs_resnet18, 1)
    conf_eff, pred_eff = torch.max(probs_eff, 1)

    ensemble_breakdown = {
        "resnet50": {
            "defect": classes[pred_r50.item()],
            "confidence": round(conf_r50.item() * 100, 2)
        },
        "resnet18": {
            "defect": classes[pred_r18.item()],
            "confidence": round(conf_r18.item() * 100, 2)
        },
        "efficientnet_b2": {
            "defect": classes[pred_eff.item()],
            "confidence": round(conf_eff.item() * 100, 2)
        }
    }


    # ========================================================
    # BACKWARD PASS (GRAD-CAM ON RESNET50 FOR PREDICTED DEFECT)
    # ========================================================

    score = outputs_resnet50[
        0,
        predicted.item()
    ]

    score.backward()


    # ========================================================
    # REMOVE HOOKS
    # ========================================================

    forward_handle.remove()

    backward_handle.remove()


    # ========================================================
    # GET ACTIVATIONS / GRADIENTS
    # ========================================================

    activation = activations[0]

    gradient = gradients[0]


    # ========================================================
    # GRAD-CAM WEIGHTS
    # ========================================================

    weights = gradient.mean(
        dim=(2, 3),
        keepdim=True
    )


    # ========================================================
    # GENERATE CAM
    # ========================================================

    cam = (
        weights
        *
        activation
    ).sum(
        dim=1
    )


    # ========================================================
    # RELU
    # ========================================================

    cam = torch.relu(
        cam
    )


    # ========================================================
    # CONVERT TO NUMPY
    # ========================================================

    cam = (
        cam[0]
        .detach()
        .cpu()
        .numpy()
    )


    # ========================================================
    # NORMALIZE CAM
    # ========================================================

    cam = cam - cam.min()

    if cam.max() != 0:

        cam = (
            cam
            /
            cam.max()
        )


    # ========================================================
    # GET LOCALIZATION
    # ========================================================

    localization = get_defect_location(
        cam,
        wafer_mask
    )

    defect_location = (
        localization[
            "location"
        ]
    )

    affected_area = (
        localization[
            "affected_area"
        ]
    )


    # ========================================================
    # PREPARE CAM FOR HEATMAP
    #
    # Upscale the CAM to 224 x 224 and remove activation
    # outside the wafer.
    # ========================================================

    cam_image = Image.fromarray(
        cam.astype(np.float32),
        mode="F"
    )

    cam_image = cam_image.resize(
        (224, 224),
        Image.Resampling.BILINEAR
    )

    display_cam = np.array(
        cam_image
    )

    display_cam = (
        display_cam
        -
        display_cam.min()
    )

    if display_cam.max() > 0:

        display_cam = (
            display_cam
            /
            display_cam.max()
        )

    # Remove background activation
    display_cam = np.where(
        wafer_mask,
        display_cam,
        0
    )


    # ========================================================
    # CREATE GRAD-CAM HEATMAP
    # ========================================================

    heatmap = cm.jet(
        display_cam
    )[:, :, :3]

    heatmap = np.uint8(
        heatmap * 255
    )


    # ========================================================
    # CREATE HEATMAP IMAGE
    # ========================================================

    heatmap_image = Image.fromarray(
        heatmap
    )


    # ========================================================
    # CREATE WAFER MASK IMAGE
    # ========================================================

    wafer_mask_image = Image.fromarray(
        (
            wafer_mask.astype(
                np.uint8
            )
            *
            255
        )
    )


    # ========================================================
    # RESIZE TO ORIGINAL IMAGE SIZE
    # ========================================================

    heatmap_image = heatmap_image.resize(
        original_image.size,
        Image.Resampling.BILINEAR
    )

    wafer_mask_image = wafer_mask_image.resize(
        original_image.size,
        Image.Resampling.NEAREST
    )


    # ========================================================
    # REMOVE HEATMAP OUTSIDE WAFER
    #
    # Outside the wafer, retain the original image instead
    # of showing blue/red Grad-CAM colors.
    # ========================================================

    masked_heatmap = Image.composite(
        heatmap_image,
        original_image,
        wafer_mask_image
    )


    # ========================================================
    # OVERLAY HEATMAP
    # ========================================================

    overlay = Image.blend(
        original_image,
        masked_heatmap,
        alpha=0.5
    )


    # ========================================================
    # SAVE HEATMAP
    # ========================================================

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

    overlay.save(
        heatmap_path
    )


    # ========================================================
    # DEFECT
    # ========================================================

    defect = classes[
        predicted.item()
    ]


    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence_percentage = (
        confidence.item()
        *
        100
    )


    # ========================================================
    # CONFIDENCE STATUS
    # ========================================================

    if confidence_percentage >= 80:

        confidence_status = (
            "High Confidence"
        )

        confidence_warning = None

    elif confidence_percentage >= 60:

        confidence_status = (
            "Moderate Confidence"
        )

        confidence_warning = (
            "Prediction is moderately confident."
        )

    else:

        confidence_status = (
            "Low Confidence"
        )

        confidence_warning = (
            "Low confidence prediction. "
            "Manual inspection recommended."
        )


    # ========================================================
    # LOAD HISTORY
    # ========================================================

    try:

        with open(
            history_file,
            "r"
        ) as f:

            history = json.load(
                f
            )

    except:

        history = []


    # ========================================================
    # CREATE HISTORY RECORD
    # ========================================================

    record = {

        "id":
            len(history) + 1,

        "wafer_id":
            file.filename,

        "defect":
            defect,

        "confidence":
            round(
                confidence_percentage,
                2
            ),

        "confidence_status":
            confidence_status,

        "confidence_warning":
            confidence_warning,

        "location":
            defect_location,

        "affected_area":
            affected_area,

        "timestamp":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "heatmap":
            f"/heatmaps/{heatmap_filename}",

        "ensemble_breakdown":
            ensemble_breakdown
    }


    # ========================================================
    # SAVE HISTORY
    # ========================================================

    history.append(
        record
    )

    with open(
        history_file,
        "w"
    ) as f:

        json.dump(
            history,
            f,
            indent=4
        )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "defect":
            defect,

        "confidence":
            round(
                confidence_percentage,
                2
            ),

        "confidence_status":
            confidence_status,

        "confidence_warning":
            confidence_warning,

        "location":
            defect_location,

        "affected_area":
            affected_area,

        "heatmap":
            f"/heatmaps/{heatmap_filename}",

        "wafer_id":
            file.filename,

        "timestamp":
            record["timestamp"],

        "ensemble_breakdown":
            ensemble_breakdown
    }


# ============================================================
# GET HISTORY
# ============================================================

@app.get("/history")
def get_history():

    try:

        with open(
            history_file,
            "r"
        ) as f:

            history = json.load(
                f
            )

    except:

        history = []


    return {

        "total_inspections":
            len(history),

        "inspections":
            history
    }


# ============================================================
# CLEAR HISTORY
# ============================================================

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

        "message":
            "Inspection history cleared successfully"
    }