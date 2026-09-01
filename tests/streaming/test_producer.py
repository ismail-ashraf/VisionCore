import time
from src.vision_core.streaming.buffer import StreamingBuffer
from src.vision_core.streaming.producer import StreamProducer

class FakeVideoSource:

    def __init__(self):
        self.frames = ["frame1", "frame2", "frame3"]

    def read(self):
        if not self.frames:
            return False, None

        return True, self.frames.pop(0)


def test_producer_puts_frames_into_buffer():
    source = FakeVideoSource()
    buffer = StreamingBuffer()

    producer = StreamProducer(
        source,
        buffer
    )

    producer.start()
    producer.stop()
    producer.join()

    assert buffer.get_latest() == "frame3"