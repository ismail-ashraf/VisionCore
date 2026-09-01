import time

from src.vision_core.streaming.buffer import StreamingBuffer
from src.vision_core.streaming.consumer import StreamConsumer


class FakeDetector:

    def __init__(self):
        self.processed_frames = []

    def predict(self, frame):

        self.processed_frames.append(frame)

        return "normal", 0.2


def test_consumer_sends_frame_to_detector():

    buffer = StreamingBuffer()
    detector = FakeDetector() #type:ignore


    consumer = StreamConsumer(
        buffer,
        detector # type:ignore
    )

    consumer.start()

    buffer.put("frame1")

    time.sleep(0.1)

    consumer.stop()

    assert detector.processed_frames == ["frame1"]