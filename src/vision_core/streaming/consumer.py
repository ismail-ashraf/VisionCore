import threading
from .buffer import _STOP,StreamingBuffer
from vision_core.inference.detector_consumer import AnomalyDetector
from vision_core.detection.detector import YOLODetector


class StreamConsumer:
    def __init__(self , buffer:StreamingBuffer,anomaly_detector:AnomalyDetector,yolo_detector:YOLODetector):
        self._buffer = buffer
        self._anomaly_detector = anomaly_detector
        self._yolo_detector = yolo_detector
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="stream-consumer"
        )

    def _run(self):
        while not self._stop_event.is_set():

            frame = self._buffer.get_latest()

            if frame is _STOP:
                break

            detections = self._yolo_detector.predict(frame)

            for detection in detections:
                bbox = detection.bbox
                x1, y1, x2, y2 = map(int, bbox)

                category = detection.class_name

                crop = frame[y1:y2, x1:x2]

                if crop.size == 0:
                    continue

                prediction, score = self._anomaly_detector.predict(
                    crop,
                    category
                )

                print(
                    f"Category: {category} | "
                    f"Confidence: {detection.confidence:.2f} | "
                    f"Anomaly: {prediction} | "
                    f"Score: {score}"
                )

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._buffer.stop_consumer()
        self._thread.join()