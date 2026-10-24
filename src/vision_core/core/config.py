import os
from dotenv import load_dotenv

load_dotenv()

# YOLO model configuration
YOLO_MODEL_WEIGHTS = os.getenv("YOLO_MODEL_WEIGHTS")

if not YOLO_MODEL_WEIGHTS:
    raise ValueError(
        "YOLO_MODEL_WEIGHTS is missing from your .env file!"
    )

# Detection confidence threshold
try:
    CONFIDENCE_THRESHOLD = float(
        os.getenv("CONFIDENCE_THRESHOLD", "0.5")
    )
except ValueError as exc:
    raise ValueError(
        "CONFIDENCE_THRESHOLD must be a valid number!"
    ) from exc

if not 0.0 <= CONFIDENCE_THRESHOLD <= 1.0:
    raise ValueError(
        "CONFIDENCE_THRESHOLD must be between 0.0 and 1.0!"
    )

# Inference device
DEVICE = os.getenv("DEVICE", "cpu")

if not DEVICE:
    raise ValueError(
        "DEVICE is missing from your .env file!"
    )
