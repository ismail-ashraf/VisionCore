import threading


class StreamProducer:
    def __init__(self,source,buffer):
        self._source = source
        self._buffer = buffer
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="stream-producer"
        )

    def _run(self):
        while not self._stop_event.is_set():
            success,frame = self._source.read()

            if not success:
                break

            self._buffer.put(frame)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def join(self):
        self._thread.join()