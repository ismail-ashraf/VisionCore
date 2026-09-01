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