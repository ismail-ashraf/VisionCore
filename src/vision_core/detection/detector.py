
import cv2
import torch
import threading

from vision_core.detection.schema import Detection


class YOLODetector:
    def __init__(
        self,
        model,
        confidence_threshold=0.5,
        device="cuda",
    ):
        self.model = model
        self._validate_confidence(confidence_threshold)

        self.confidence_threshold = confidence_threshold
        self.device = device

        self._settings_lock = threading.Lock()

    @staticmethod
    def _validate_confidence(value):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            raise ValueError(
                "confidence_threshold must be between 0 and 1"
            )

    def update_settings(self, confidence_threshold=None):
        if confidence_threshold is None:
            return

        self._validate_confidence(confidence_threshold)

        with self._settings_lock:
            self.confidence_threshold = float(
                confidence_threshold
            )

    def _get_confidence_threshold(self):
        with self._settings_lock:
            return self.confidence_threshold

    def predict(self, frame):
        if frame is None or frame.size == 0:
            raise ValueError("Input frame is empty or None")

        confidence_threshold = self._get_confidence_threshold()

        try:
            with torch.inference_mode():
                results = self.model.predict(
                    frame,
                    conf=confidence_threshold,
                    device=self.device,
                    verbose=False,
                )

            result = results[0]
            detections = []

            for box in result.boxes:
                bbox = box.xyxy[0].tolist()
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                class_name = result.names[class_id]

                detections.append(
                    Detection(
                        bbox=bbox,
                        class_id=class_id,
                        confidence=confidence,
                        class_name=class_name,
                    )
                )

            return detections

        except Exception as exc:
            raise RuntimeError("YOLO inference failed") from exc

    def predict_batch(self, frames: list):
        if frames is None or len(frames) == 0:
            raise ValueError("Input frames is empty or None")

        for frame in frames:
            if frame is None or frame.size == 0:
                raise ValueError("Input frame is empty or None")

        confidence_threshold = self._get_confidence_threshold()

        try:
            with torch.inference_mode():
                results = self.model.predict(
                    frames,
                    conf=confidence_threshold,
                    device=self.device,
                    verbose=False,
                )

            batch_detections = []

            for frame in results:
                detections = []

                for box in frame.boxes:
                    bbox = box.xyxy[0].tolist()
                    class_id = int(box.cls[0].item())
                    confidence = float(box.conf[0].item())
                    class_name = frame.names[class_id]

                    detections.append(
                        Detection(
                            bbox=bbox,
                            class_id=class_id,
                            confidence=confidence,
                            class_name=class_name,
                        )
                    )

                batch_detections.append(detections)

            return batch_detections

        except Exception as exc:
            raise RuntimeError("YOLO inference failed") from exc

    @staticmethod
    def draw_detections(frame, detections):
        for detection in detections:
            x1, y1, x2, y2 = map(int, detection.bbox)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"{detection.class_name} {detection.confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        return frame
