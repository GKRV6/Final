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
        "http://localhost:5174"
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

model_path = os.path.join(
    project_root,
    "models",
    "resnet50_wafer.pth"
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
# LOAD RESNET50
# ============================================================

model = models.resnet50(
    weights=None
)

model.fc = torch.nn.Linear(
    model.fc.in_features,
    8
)

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

print(
    "ResNet50 model loaded successfully"
)


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

transform = transforms.Compose([
    transforms.Grayscale(
        num_output_channels=3
    ),

    transforms.Resize(
        (224, 224)
    ),

    transforms.ToTensor()
])


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
            "ResNet50",

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
    # PREPROCESS IMAGE
    # ========================================================

    image_tensor = transform(
        original_image
    ).unsqueeze(
        0
    ).to(
        device
    )


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
    # TARGET LAYER
    # ========================================================

    target_layer = model.layer4[-1]


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
    # FORWARD PASS
    # ========================================================

    model.zero_grad()

    outputs = model(
        image_tensor
    )


    # ========================================================
    # PROBABILITIES
    # ========================================================

    probabilities = torch.softmax(
        outputs,
        dim=1
    )

    confidence, predicted = torch.max(
        probabilities,
        1
    )


    # ========================================================
    # BACKWARD PASS
    # ========================================================

    score = outputs[
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
            f"/heatmaps/{heatmap_filename}"
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
            record["timestamp"]
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