from collections import deque
import threading

_STOP = object()


class StreamingBuffer:
    def __init__(self):
        self._buffer = deque(maxlen=1)
        self._condition = threading.Condition()


    def put(self,frame):
        with self._condition:
            self._buffer.append(frame)
            self._condition.notify()

    def get_latest(self):
        with self._condition:
            while not self._buffer:
                self._condition.wait()

            return self._buffer.pop()

    def stop_waiting_to_close(self):
        with self._condition:
            self._condition.notify()

    def stop_consumer(self):
        with self._condition:
            self._buffer.append(_STOP)
            self._condition.notify()