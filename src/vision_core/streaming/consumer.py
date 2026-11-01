
import threading
import cv2

from .buffer import _STOP, StreamingBuffer
from vision_core.inference.dynamic_batcher import DynamicBatcher
from vision_core.tracking.tracker import Tracker
from concurrent.futures import TimeoutError
from vision_core.monitoring.drift_monitor import DriftMonitor


class StreamConsumer:
    def __init__(
        self,
        camera_id,
        buffer: StreamingBuffer,
        batcher: DynamicBatcher,
        display_manager,
        drift_window_size=1000,
        drift_monitor_interval=30,
    ):
        self.camera_id = camera_id
        self._buffer = buffer
        self._batcher = batcher
        self._stop_event = threading.Event()
        self._display_manager = display_manager

        self._drift_monitor = DriftMonitor(
            window_size=drift_window_size,
            monitor_interval=drift_monitor_interval,
        )

        # Each stream has its own tracker.
        self._tracker = Tracker(
            max_distance=80.0,
            max_missed_frames=2,
        )

        self._thread = threading.Thread(
            target=self._run,
            name="stream-consumer",
        )

    def _run(self):
        try:
            while not self._stop_event.is_set():
                frame = self._buffer.get_latest()

                if frame is _STOP:
                    break

                future = self._batcher.submit(
                    camera_id=self.camera_id,
                    frame=frame,
                )

                self._drift_monitor.update(frame)

                while not self._stop_event.is_set():
                    try:
                        detections = future.result(timeout=0.1)
                        break

                    except TimeoutError:
                        continue

                else:
                    break

                tracks = self._tracker.update(detections)

                display_frame = frame.copy()

                for track in tracks:
                    if not track.is_updated:
                        continue

                    x1, y1, x2, y2 = map(int, track.bbox)

                    cv2.rectangle(
                        display_frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    label = (
                        f"{track.class_name} "
                        f"{track.confidence:.2f} "
                        f"ID:{track.track_id}"
                    )

                    cv2.putText(
                        display_frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                self._display_manager.update(
                    camera_id=self.camera_id,
                    frame=display_frame,
                )

        except Exception as exc:
            print(f"StreamConsumer error: {exc}")

    def start(self):
        self._drift_monitor.start()
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._buffer.stop_consumer()

        if self._thread.is_alive():
            self._thread.join()

        self._drift_monitor.stop()
