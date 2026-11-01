
import threading
import cv2
import time
import logging

from vision_core.inference.dynamic_batcher import DynamicBatcher
from vision_core.streaming.buffer import StreamingBuffer
from vision_core.streaming.producer import StreamProducer
from vision_core.streaming.consumer import StreamConsumer


class StreamManager:
    def __init__(
        self,
        batcher: DynamicBatcher,
        display_manager,
        logger=None,
        drift_window_size=1000,
        drift_monitor_interval=30,
    ):
        self._batcher = batcher
        self._display_manager = display_manager
        self._logger = logger or logging.getLogger(
            "vision_core.system_events"
        )

        self._drift_window_size = drift_window_size
        self._drift_monitor_interval = float(drift_monitor_interval)

        self.cameras = {}
        self._starting_cameras = set()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._shutting_down = False

    def add_camera(self, camera_id, source_url):

        # Reserve camera ID
        with self._condition:
            if self._shutting_down:
                raise RuntimeError("StreamManager is shutting down")

            if (
                camera_id in self.cameras
                or camera_id in self._starting_cameras
            ):
                raise ValueError(
                    f"Camera {camera_id} already exists or is starting"
                )

            self._starting_cameras.add(camera_id)

        source = None
        producer = None
        consumer = None

        try:
            # Open video source
            source = cv2.VideoCapture(source_url)

            if not source.isOpened():
                raise RuntimeError(
                    f"Could not open camera: {camera_id}"
                )

            # Create camera components
            buffer = StreamingBuffer()

            producer = StreamProducer(
                source=source,
                buffer=buffer,
            )

            # Read current drift settings
            with self._lock:
                drift_window_size = self._drift_window_size
                drift_monitor_interval = self._drift_monitor_interval

            consumer = StreamConsumer(
                camera_id=camera_id,
                buffer=buffer,
                batcher=self._batcher,
                display_manager=self._display_manager,
                drift_window_size=drift_window_size,
                drift_monitor_interval=drift_monitor_interval,
            )

            # Start camera threads
            producer.start()
            consumer.start()

            # Register camera only after successful startup
            with self._condition:
                # Apply the latest settings in case they changed
                # while this camera was starting.
                consumer._drift_monitor.update_settings(
                    window_size=self._drift_window_size,
                    monitor_interval=self._drift_monitor_interval,
                )

                self.cameras[camera_id] = {
                    "source": source,
                    "buffer": buffer,
                    "producer": producer,
                    "consumer": consumer,
                    "drift_monitor": consumer._drift_monitor,
                }

            self._logger.info(
                f"Camera {camera_id} connected successfully",
                extra={
                    "event": "CAMERA_CONNECTED",
                    "camera_id": camera_id,
                },
            )

        except Exception:
            self._logger.exception(
                f"Failed to connect camera {camera_id}",
                extra={
                    "event": "CAMERA_CONNECTION_FAILED",
                    "camera_id": camera_id,
                },
            )

            # Stop consumer if created
            if consumer is not None:
                consumer.stop()

            # Stop producer if created
            if producer is not None:
                producer.stop()

            # Release video source
            if source is not None:
                source.release()

            # Remove partially registered camera
            with self._lock:
                self.cameras.pop(camera_id, None)

            raise

        finally:
            # Release reservation and notify waiting threads
            with self._condition:
                self._starting_cameras.discard(camera_id)
                self._condition.notify_all()

    def stop_camera(self, camera_id):

        # Get camera without removing it from the manager
        with self._lock:
            camera = self.cameras.get(camera_id)

        if camera is None:
            raise ValueError(f"Camera {camera_id} not found")

        producer = camera["producer"]
        consumer = camera["consumer"]
        source = camera["source"]

        errors = []

        # Stop producer and consumer independently
        for resource in (producer, consumer):
            try:
                resource.stop()
            except Exception as exc:
                errors.append(exc)

        # Release the video source
        try:
            source.release()
        except Exception as exc:
            errors.append(exc)

        # Keep the camera registered if cleanup failed
        if errors:
            self._logger.error(
                f"Failed to completely stop camera {camera_id}: {errors[0]}",
                extra={
                    "event": "CAMERA_STOP_FAILED",
                    "camera_id": camera_id,
                },
            )

            raise RuntimeError(
                f"Failed to completely stop camera {camera_id}"
            ) from errors[0]

        self._display_manager.remove(camera_id)

        # Remove camera only after successful cleanup
        with self._lock:
            self.cameras.pop(camera_id, None)

        self._logger.info(
            f"Camera {camera_id} stopped successfully",
            extra={
                "event": "CAMERA_STOPPED",
                "camera_id": camera_id,
            },
        )

    def stop_all(self):

        with self._condition:
            self._shutting_down = True

            while self._starting_cameras:
                self._condition.wait()

            camera_ids = list(self.cameras.keys())

        errors = []

        for camera_id in camera_ids:
            try:
                self.stop_camera(camera_id)
            except Exception as exc:
                errors.append(exc)

        if errors:
            raise RuntimeError(
                f"Failed to stop {len(errors)} camera(s)"
            ) from errors[0]

    def list_cameras(self):
        with self._lock:
            return [
                {
                    "camera_id": camera_id,
                    "status": (
                        "running"
                        if camera["producer"]._thread.is_alive()
                        and camera["consumer"]._thread.is_alive()
                        else "stopped"
                    ),
                }
                for camera_id, camera in self.cameras.items()
            ]

    def update_drift_settings(
        self,
        window_size=None,
        monitor_interval=None,
    ):
        # Validate settings before applying any changes
        if window_size is not None:
            if (
                isinstance(window_size, bool)
                or not isinstance(window_size, int)
                or window_size <= 0
            ):
                raise ValueError(
                    "window_size must be a positive integer"
                )

        if monitor_interval is not None:
            if (
                isinstance(monitor_interval, bool)
                or not isinstance(monitor_interval, (int, float))
                or monitor_interval <= 0
            ):
                raise ValueError(
                    "monitor_interval must be positive"
                )

        # Update manager settings and get current monitors
        with self._lock:
            if window_size is not None:
                self._drift_window_size = window_size

            if monitor_interval is not None:
                self._drift_monitor_interval = float(
                    monitor_interval
                )

            cameras = {
                camera_id: camera["drift_monitor"]
                for camera_id, camera in self.cameras.items()
            }

            current_window_size = self._drift_window_size
            current_interval = self._drift_monitor_interval

        # Update monitors outside the manager lock
        for monitor in cameras.values():
            monitor.update_settings(
                window_size=current_window_size,
                monitor_interval=current_interval,
            )

    def get_drift_insights(self, camera_id=None):

        with self._lock:
            if camera_id is not None:
                camera = self.cameras.get(camera_id)

                if camera is None:
                    raise ValueError(
                        f"Camera {camera_id} not found"
                    )

                cameras = {
                    camera_id: camera["drift_monitor"]
                }

            else:
                cameras = {
                    cam_id: camera["drift_monitor"]
                    for cam_id, camera in self.cameras.items()
                }

        insights = []

        for cam_id, monitor in cameras.items():
            report = monitor.get_latest_report()

            insights.append({
                "camera_id": cam_id,
                "monitoring_status": (
                    "ready" if report is not None else "collecting"
                ),
                "sample_count": monitor.sample_count,
                "window_size": monitor.window_size,
                "features": (
                    report["features"] if report is not None else None
                ),
            })

        return insights

    def get_camera_health(self):
        with self._lock:
            cameras = dict(self.cameras)

        health = []

        for camera_id, camera in cameras.items():
            producer = camera["producer"]
            consumer = camera["consumer"]

            producer_health = producer.get_health()

            producer_alive = producer._thread.is_alive()
            consumer_alive = consumer._thread.is_alive()

            last_frame_at = producer_health["last_frame_at"]

            if not producer_alive:
                status = "stopped"

            elif not consumer_alive:
                status = "degraded"

            elif last_frame_at is None:
                status = "starting"

            else:
                elapsed = time.time() - last_frame_at

                if elapsed > 3:
                    status = "stale"
                else:
                    status = "healthy"

            health.append({
                "camera_id": camera_id,
                "health_status": status,
                "last_frame_at": last_frame_at,
                "seconds_since_last_frame": (
                    round(time.time() - last_frame_at, 2)
                    if last_frame_at is not None
                    else None
                ),
                "producer_thread_alive": producer_alive,
                "consumer_thread_alive": consumer_alive,
            })

        return health

    def get_inference_metrics(self):
        return self._batcher.get_metrics()

    def get_camera_frame(self, camera_id):
        with self._lock:
            if camera_id not in self.cameras:
                raise ValueError(f"Camera {camera_id} not found")

        return self._display_manager.get_frame(camera_id)
