import threading
import cv2
from .buffer import _STOP, StreamingBuffer
from vision_core.detection.detector import YOLODetector
from vision_core.tracking.tracker import Tracker


class StreamConsumer:
    def __init__(self,buffer: StreamingBuffer,yolo_detector: YOLODetector,):
        self._buffer = buffer
        self._yolo_detector = yolo_detector
        self._stop_event = threading.Event()

        self._tracker = Tracker()

        self._thread = threading.Thread(
            target=self._run,
            name="stream-consumer",
        )

    def _run(self):
        try:
            print("Consumer: thread started")

            while not self._stop_event.is_set():
                print("Consumer: waiting for frame")
                frame = self._buffer.get_latest()
                print(f"Consumer: got frame or STOP = {frame is _STOP}")

                if frame is _STOP:
                    print("Consumer: received STOP")
                    break

                print("Consumer: frame received", frame.shape)

                detections = self._yolo_detector.predict(frame)
                print(f"Consumer: YOLO returned {len(detections)} detections")

                tracks = self._tracker.update(detections)
                print(f"Consumer: Tracker returned {len(tracks)} tracks")

                # 3. Copy frame for visualization
                display_frame = frame.copy()

                # 4. Draw bounding boxes and track IDs
                for track in tracks:
                    x1, y1, x2, y2 = map(int, track.bbox)

                    cv2.rectangle(
                        display_frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    label = f"ID: {track.track_id}"

                    cv2.putText(
                        display_frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                # 5. Display tracking result
                cv2.imshow(
                    "VisionCore - YOLO Tracking",
                    display_frame,
                )
                print("Consumer: imshow reached")

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self._stop_event.set()
                    print("Consumer: waitKey reached")
                    break

        finally:
            cv2.destroyAllWindows()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._buffer.stop_consumer()

        if self._thread.is_alive():
            self._thread.join()
