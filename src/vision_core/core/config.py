import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VISIONCORE_MODEL_PATH = os.getenv("VISIONCORE_MODEL_PATH")
VISIONCORE_MEMORY_BANK_PATH = os.getenv("VISIONCORE_MEMORY_BANK_PATH")

if not VISIONCORE_MODEL_PATH:
    raise ValueError(
        "VISIONCORE_MODEL_PATH is missing from your .env file!"
    )

YOLO_MODEL_WEIGHTS = os.getenv('YOLO_MODEL_WEIGHTS')

if not YOLO_MODEL_WEIGHTS:
    raise ValueError(
        "YOLO_MODEL_WEIGHTS is missing from your .env file!"
    )

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD","0.5"))

if not CONFIDENCE_THRESHOLD:
    raise ValueError(
        "CONFIDENCE_THRESHOLD is missing from your .env file!"
    )
DEVICE = os.getenv("DEVICE" , 'cpu')

if not DEVICE:
    raise ValueError(
        "DEVICE is missing from your .env file!"
    )