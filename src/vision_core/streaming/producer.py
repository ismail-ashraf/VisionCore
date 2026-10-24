
import threading


class StreamProducer:
    def __init__(self, source, buffer):
        self._source = source
        self._buffer = buffer
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="stream-producer",
        )

    def _run(self):
        frames_read = 0

        try:
            while not self._stop_event.is_set():
                success, frame = self._source.read()

                if not success:
                    print("Producer: source.read() returned False")
                    break

                frames_read += 1
                self._buffer.put(frame)

        finally:
            print(f"Producer: total frames read = {frames_read}")
            print("Producer: closing buffer now")
            self._buffer.close()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

        if self._thread.is_alive():
            self._thread.join()

        self._buffer.close()

    def join(self):
        self._thread.join()
