import queue
import threading
from concurrent.futures import Future
import time


class DynamicBatcher:
    def __init__(self, detector, max_batch_size=4, max_wait_ms=15):
        self.detector = detector
        self.max_batch_size = max_batch_size
        self.max_wait_seconds = max_wait_ms / 1000

        self.request_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self._metrics_lock = threading.Lock()

        # Inference metrics
        self._total_batches = 0
        self._total_frames = 0
        self._total_inference_time = 0.0
        self._last_latency_ms = 0.0

        # Queue metrics
        self._max_queue_size = 0
        self._total_wait_time = 0.0
        self._last_wait_time_ms = 0.0

        # Error metrics
        self._total_errors = 0
        self._total_failed_frames = 0
        self._last_error = None
        self._last_error_at = None

    def submit(self, camera_id, frame):
        if self.stop_event.is_set():
            raise RuntimeError("DynamicBatcher is stopping")

        submitted_at = time.perf_counter()

        future = Future()
        self.request_queue.put(
            (camera_id, frame, future, submitted_at)
        )

        with self._metrics_lock:
            self._max_queue_size = max(
                self._max_queue_size,
                self.request_queue.qsize()
            )

        return future

    def _collect_batch(self):
        batch = []
        start_time = time.monotonic()

        while len(batch) < self.max_batch_size:
            elapsed = time.monotonic() - start_time
            remaining = self.max_wait_seconds - elapsed

            if remaining <= 0:
                break

            try:
                request = self.request_queue.get(timeout=remaining)
            except queue.Empty:
                break

            batch.append(request)

        return batch

    def _process_batch(self, batch):
        if not batch:
            return

        frames = [request[1] for request in batch]

        # Measure request waiting time before inference
        inference_start_time = time.perf_counter()

        wait_times = [
            (inference_start_time - request[3]) * 1000
            for request in batch
        ]

        average_wait_time = sum(wait_times) / len(wait_times)

        with self._metrics_lock:
            self._total_wait_time += sum(wait_times)
            self._last_wait_time_ms = average_wait_time

        # Measure inference execution time only
        start_time = time.perf_counter()

        try:
            batch_detections = self.detector.predict_batch(frames)

            inference_time = time.perf_counter() - start_time
            latency_ms = inference_time * 1000

            batch_size = len(batch)

            with self._metrics_lock:
                self._total_batches += 1
                self._total_frames += batch_size
                self._total_inference_time += inference_time
                self._last_latency_ms = latency_ms

            for index, request in enumerate(batch):
                camera_id, frame, future, submitted_at = request

                detections = batch_detections[index]
                future.set_result(detections)

        except Exception as exc:
            with self._metrics_lock:
                self._total_errors += 1
                self._total_failed_frames += len(batch)
                self._last_error = f"{type(exc).__name__}: {str(exc)}"
                self._last_error_at = time.time()

            for camera_id, frame, future, submitted_at in batch:
                future.set_exception(exc)

    def _run(self):
        while True:
            batch = self._collect_batch()

            if self.stop_event.is_set():
                while not self.request_queue.empty():
                    try:
                        request = self.request_queue.get_nowait()
                        batch.append(request)
                    except queue.Empty:
                        break

            if batch:
                self._process_batch(batch)

            if self.stop_event.is_set() and self.request_queue.empty():
                break

    def start(self):
        self.worker_thread = threading.Thread(
            target=self._run,
            name="dynamic-batcher",
            daemon=True
        )

        self.worker_thread.start()

    def stop(self):
        self.stop_event.set()

        if self.worker_thread is not None:
            self.worker_thread.join()

    def get_metrics(self):
        with self._metrics_lock:
            total_batches = self._total_batches
            total_frames = self._total_frames
            total_inference_time = self._total_inference_time
            last_latency_ms = self._last_latency_ms
            max_queue_size = self._max_queue_size
            total_wait_time = self._total_wait_time
            last_wait_time_ms = self._last_wait_time_ms
            total_errors = self._total_errors
            total_failed_frames = self._total_failed_frames
            last_error = self._last_error
            last_error_at = self._last_error_at

        average_latency_ms = (
            total_inference_time / total_batches * 1000
            if total_batches > 0
            else 0.0
        )

        throughput_fps = (
            total_frames / total_inference_time
            if total_inference_time > 0
            else 0.0
        )

        average_wait_time_ms = (
            total_wait_time / total_frames
            if total_frames > 0
            else 0.0
        )

        return {
            "total_batches": total_batches,
            "total_frames": total_frames,
            "average_batch_latency_ms": average_latency_ms,
            "last_latency_ms": last_latency_ms,
            "throughput_fps": throughput_fps,
            "average_wait_time_ms": average_wait_time_ms,
            "last_wait_time_ms": last_wait_time_ms,
            "queue_size": self.request_queue.qsize(),
            "max_queue_size": max_queue_size,

            "errors": {
                "total_errors": total_errors,
                "total_failed_frames": total_failed_frames,
                "last_error": last_error,
                "last_error_at": last_error_at,
            }
        }
