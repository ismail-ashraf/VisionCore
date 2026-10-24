import threading
from .buffer import _STOP,StreamingBuffer
from vision_core.inference.detector_consumer import AnomalyDetector
from vision_core.detection.detector import YOLODetector
from vision_core.tracking.tracker import Tracker
import cv2


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

        self._tracker = Tracker()

    def _run(self):
        try:
            while not self._stop_event.is_set():

                frame = self._buffer.get_latest()

                if frame is _STOP:
                    break

                # 1. Detect vehicles using YOLO
                detections = self._yolo_detector.predict(frame)

                # 2. Track vehicles across frames
                tracks = self._tracker.update(detections)

                # 3. Copy the frame so we can draw on it
                display_frame = frame.copy()

                # 4. Draw bounding boxes and IDs
                for track in tracks:
                    x1, y1, x2, y2 = map(int, track.bbox)

                    cv2.rectangle(
                        display_frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    label = f"ID: {track.track_id}"

                    cv2.putText(
                        display_frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                # 5. Display the tracking result
                cv2.imshow(
                    "VisionCore - Vehicle Tracking",
                    display_frame
                )

                # Press Q to close the display
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self._stop_event.set()
                    break

                # 6. Keep the existing anomaly detection
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

        finally:
            cv2.destroyAllWindows()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._buffer.stop_consumer()
        self._thread.join()