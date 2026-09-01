from src.vision_core.streaming.buffer import StreamingBuffer

def test_get_latest_returns_latest_frame():
    buffer = StreamingBuffer()

    frame1 = 'frame1'
    frame2 = 'frame2'

    buffer.put(frame1)
    buffer.put(frame2)

    assert buffer.get_latest() == frame2


