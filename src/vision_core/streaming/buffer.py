
from collections import deque
import threading

_STOP = object()


class StreamingBuffer:
    def __init__(self):
        self._buffer = deque(maxlen=1)
        self._condition = threading.Condition()
        self._closed = False

    def put(self, frame):
        with self._condition:
            if self._closed:
                return

            self._buffer.append(frame)
            self._condition.notify()

    def get_latest(self):
        with self._condition:
            while not self._buffer and not self._closed:
                self._condition.wait()

            if self._buffer:
                return self._buffer.pop()

            return _STOP

    def close(self):
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def stop_waiting_to_close(self):
        self.close()

    def stop_consumer(self):
        self.close()
