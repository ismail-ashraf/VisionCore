
import time

import numpy as np

from vision_core.detection.schema import Detection
from vision_core.streaming.buffer import StreamingBuffer
from vision_core.streaming.consumer import StreamConsumer


class FakeDetector:
    def __init__(self):
        self.processed_frames = []

    def predict(self, frame):
        self.processed_frames.append(frame)

        return [
            Detection(
                bbox=[10.0, 20.0, 100.0, 120.0],
                class_id=0,
                confidence=0.9,
                class_name="pothole",
            )
        ]


def test_consumer_sends_frame_to_detector():
    buffer = StreamingBuffer()
    detector = FakeDetector()

    consumer = StreamConsumer(
        buffer=buffer,
        yolo_detector=detector,  # type: ignore
    )

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    consumer.start()

    try:
        buffer.put(frame)

        deadline = time.monotonic() + 2.0

        while (
            len(detector.processed_frames) == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

    finally:
        consumer.stop()

    assert len(detector.processed_frames) == 1
    assert detector.processed_frames[0] is frame
