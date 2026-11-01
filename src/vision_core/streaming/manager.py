import threading
import cv2
from vision_core.inference.dynamic_batcher import DynamicBatcher
from vision_core.streaming.buffer import StreamingBuffer
from vision_core.streaming.producer import StreamProducer
from vision_core.streaming.consumer import StreamConsumer


class StreamManager:
    def __init__(self, batcher: DynamicBatcher, display_manager):
        self._batcher = batcher
        self._display_manager = display_manager
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

            consumer = StreamConsumer(
                camera_id=camera_id,
                buffer=buffer,
                batcher=self._batcher,
                display_manager=self._display_manager,
            )

            # Start camera threads
            producer.start()
            consumer.start()

            # Register camera only after successful startup
            with self._condition:
                self.cameras[camera_id] = {
                    "source": source,
                    "buffer": buffer,
                    "producer": producer,
                    "consumer": consumer,
                    "drift_monitor": consumer._drift_monitor,
                }

        except Exception:
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
            raise RuntimeError(
                f"Failed to completely stop camera {camera_id}"
            ) from errors[0]

        self._display_manager.remove(camera_id)

        # Remove camera only after successful cleanup
        with self._lock:
            self.cameras.pop(camera_id, None)

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