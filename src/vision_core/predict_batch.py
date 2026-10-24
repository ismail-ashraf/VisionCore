import cv2
from ultralytics import YOLO

from vision_core.detection.detector import YOLODetector
from vision_core.core.config import YOLO_MODEL_WEIGHTS


# 1. Load the model once
model = YOLO(YOLO_MODEL_WEIGHTS)

detector = YOLODetector(
    model=model,
    confidence_threshold=0.5,
    device="cuda",  # Use "cpu" if CUDA is unavailable
)

# 2. Read three images
image_paths = [
    r"C:\Users\iismmail\Downloads\1.webp",
r"C:\Users\iismmail\Downloads\2.webp",
r"C:\Users\iismmail\Downloads\3.webp",
]

frames = []

for path in image_paths:
    frame = cv2.imread(path)

    if frame is None:
        raise FileNotFoundError(f"Could not read image: {path}")

    frames.append(frame)

# 3. Run batch inference
results = detector.predict_batch(frames)

# 4. Verify the results
print("Input images:", len(frames))
print("Output results:", len(results))
print("Detections per image:", [len(detections) for detections in results])

assert len(results) == len(frames), "Output count does not match input count!"

print("Batch inference test passed!")
