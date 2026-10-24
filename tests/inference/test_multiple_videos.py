import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from vision_core.inference.dynamic_batcher import DynamicBatcher


class FakeDetector:
    """Simulates YOLO batch inference without loading a real model."""

    def __init__(self):
        self.batch_calls = []
        self.lock = threading.Lock()

    def predict_batch(self, frames):
        with self.lock:
            self.batch_calls.append(len(frames))

        # Return one result for each input frame.
        return [
            [{"frame_id": int(frame[0, 0])}]
            for frame in frames
        ]


def test_multiple_streams_share_dynamic_batcher():
    detector = FakeDetector()

    batcher = DynamicBatcher(
        detector=detector,
        max_batch_size=3,
        max_wait_ms=100,
    )

    batcher.start()

    try:
        def submit_stream_frame(frame_id):
            frame = np.full(
                (10, 10),
                frame_id,
                dtype=np.uint8,
            )

            future = batcher.submit(frame)
            return future.result(timeout=5)

        # Simulate three independent streams submitting concurrently.
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(submit_stream_frame, stream_id)
                for stream_id in (1, 2, 3)
            ]

            results = [
                future.result(timeout=10)
                for future in futures
            ]

        # Every submitted frame receives its own detections.
        returned_ids = {
            result[0]["frame_id"]
            for result in results
        }

        assert returned_ids == {1, 2, 3}

        # All frames were processed.
        assert sum(detector.batch_calls) == 3

        # Concurrent submissions should be collected into one batch
        # with these settings.
        assert detector.batch_calls == [3]

    finally:
        batcher.stop()

    assert not batcher.worker_thread.is_alive()
