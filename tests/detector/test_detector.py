
import numpy as np
import pytest
import torch

from vision_core.detection.detector import YOLODetector


class FakeBox:
    def __init__(self, bbox, class_id, confidence):
        self.xyxy = torch.tensor([bbox], dtype=torch.float32)
        self.cls = torch.tensor([class_id])
        self.conf = torch.tensor([confidence])


class FakeBoxes:
    def __init__(self, boxes=None):
        self._boxes = boxes or []

    def __iter__(self):
        return iter(self._boxes)

    def __len__(self):
        return len(self._boxes)


class FakeResult:
    def __init__(self, boxes=None):
        self.boxes = FakeBoxes(boxes)
        self.names = {
            0: "defect"
        }


class FakeModel:
    def predict(
        self,
        frame,
        conf=0.5,
        device="cpu",
        verbose=False,
        **kwargs,
    ):
        return [
            FakeResult(
                boxes=[
                    FakeBox(
                        bbox=[10.0, 20.0, 100.0, 200.0],
                        class_id=0,
                        confidence=0.91,
                    )
                ]
            )
        ]


class EmptyModel:
    def predict(
        self,
        frame,
        conf=0.5,
        device="cpu",
        verbose=False,
        **kwargs,
    ):
        return [FakeResult()]


class FailingModel:
    def predict(
        self,
        frame,
        conf=0.5,
        device="cpu",
        verbose=False,
        **kwargs,
    ):
        raise RuntimeError("Model failed")


def create_frame():
    return np.zeros(
        (640, 640, 3),
        dtype=np.uint8,
    )


def test_predict_returns_detection():
    detector = YOLODetector(
        model=FakeModel(),
        confidence_threshold=0.5,
        device="cpu",
    )

    detections = detector.predict(create_frame())

    assert len(detections) == 1

    detection = detections[0]

    assert detection.bbox == [10.0, 20.0, 100.0, 200.0]
    assert detection.class_id == 0
    assert detection.class_name == "defect"
    assert detection.confidence == pytest.approx(0.91)


def test_predict_none_frame():
    detector = YOLODetector(
        model=FakeModel(),
        confidence_threshold=0.5,
        device="cpu",
    )

    with pytest.raises(ValueError, match="Input frame is empty or None"):
        detector.predict(None)


def test_predict_no_detections():
    detector = YOLODetector(
        model=EmptyModel(),
        confidence_threshold=0.5,
        device="cpu",
    )

    detections = detector.predict(create_frame())

    assert detections == []


def test_predict_model_failure():
    detector = YOLODetector(
        model=FailingModel(),
        confidence_threshold=0.5,
        device="cpu",
    )

    with pytest.raises(RuntimeError, match="YOLO inference failed"):
        detector.predict(create_frame())
