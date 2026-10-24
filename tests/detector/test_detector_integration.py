from pathlib import Path

import cv2
from ultralytics import YOLO

from vision_core.core.config import (
    YOLO_MODEL_WEIGHTS,
    CONFIDENCE_THRESHOLD,
    DEVICE
)
from vision_core.detection.detector import YOLODetector


def test_real_yolo_detector():

    image_path = Path(
        r"C:\Users\iismmail\Downloads\000.png"
    )

    frame = cv2.imread(str(image_path))

    assert frame is not None

    model = YOLO(YOLO_MODEL_WEIGHTS)

    detector = YOLODetector(
        model=model,
        confidence_threshold=float(CONFIDENCE_THRESHOLD),
        device=DEVICE
    )

    detections = detector.predict(frame)

    assert isinstance(detections, list)

    for detection in detections:
        assert len(detection.bbox) == 4
        assert 0 <= detection.confidence <= 1
        assert isinstance(detection.class_id, int)
        assert isinstance(detection.class_name, str)

        print(detection)