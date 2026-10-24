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

    def submit(self, frame):
        if self.stop_event.is_set():
            raise RuntimeError("DynamicBatcher is stopping")

        future = Future()
        self.request_queue.put((frame, future))

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
        if len(batch) == 0:
            return

        frames = []

        for request in batch:
            frame = request[0]
            frames.append(frame)

        try:
            batch_detections = self.detector.predict_batch(frames)

            for index in range(len(batch)):
                request = batch[index]

                future = request[1]
                detections = batch_detections[index]

                future.set_result(detections)

        except Exception as exc:
            for request in batch:
                future = request[1]
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

            if len(batch) > 0:
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
        self.worker_thread.join()