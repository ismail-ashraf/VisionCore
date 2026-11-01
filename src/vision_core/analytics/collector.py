
import logging
import threading
import time

from vision_core.storage.database import Database
from vision_core.streaming.manager import StreamManager


logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(
        self,
        stream_manager: StreamManager,
        database: Database,
        interval: float = 10.0,
    ):
        self.stream_manager = stream_manager
        self.database = database

        self._validate_interval(interval)
        self.interval = float(interval)

        self._stop_event = threading.Event()
        self._settings_changed = threading.Event()
        self._settings_lock = threading.Lock()

        self._thread = None

    @staticmethod
    def _validate_interval(interval):
        if (
            isinstance(interval, bool)
            or not isinstance(interval, (int, float))
            or interval <= 0
        ):
            raise ValueError("interval must be a positive number")

    def update_interval(self, interval: float):
        self._validate_interval(interval)

        with self._settings_lock:
            self.interval = float(interval)
            self._settings_changed.set()

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._settings_changed.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="MetricsCollector",
            daemon=True,
        )
        self._thread.start()

        logger.info("MetricsCollector started")

    def stop(self):
        self._stop_event.set()
        self._settings_changed.set()

        if self._thread is not None:
            self._thread.join(timeout=self.interval + 5)

        logger.info("MetricsCollector stopped")

    def _run(self):
        previous_metrics = (
            self.stream_manager.get_inference_metrics()
        )
        previous_time = time.monotonic()

        while not self._stop_event.is_set():

            # Read the current interval safely
            with self._settings_lock:
                current_interval = self.interval
                self._settings_changed.clear()

            # Wait until the interval expires or settings change
            settings_changed = self._settings_changed.wait(
                current_interval
            )

            if self._stop_event.is_set():
                break

            # Recalculate the waiting period using the new interval
            if settings_changed:
                continue

            try:
                current_metrics = (
                    self.stream_manager.get_inference_metrics()
                )
                current_time = time.monotonic()

                elapsed_time = current_time - previous_time

                previous_frames = previous_metrics["total_frames"]
                current_frames = current_metrics["total_frames"]

                frames_delta = current_frames - previous_frames

                if frames_delta < 0:
                    frames_delta = 0

                throughput_fps = (
                    frames_delta / elapsed_time
                    if elapsed_time > 0
                    else 0.0
                )

                self._save_performance_snapshot(
                    metrics=current_metrics,
                    throughput_fps=throughput_fps,
                )

                previous_metrics = current_metrics
                previous_time = current_time

            except Exception:
                logger.exception(
                    "Failed to collect performance metrics"
                )

    def _save_performance_snapshot(
        self,
        metrics: dict,
        throughput_fps: float,
    ):
        errors = metrics["errors"]

        with self.database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO performance_snapshots (
                    timestamp,
                    throughput_fps,
                    average_batch_latency_ms,
                    average_wait_time_ms,
                    queue_size,
                    total_errors
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    throughput_fps,
                    metrics["average_batch_latency_ms"],
                    metrics["average_wait_time_ms"],
                    metrics["queue_size"],
                    errors["total_errors"],
                ),
            )
