import threading
import time
import cv2


class StreamProducer:
    def __init__(self, source, buffer):
        self._source = source
        self._buffer = buffer
        self._stop_event = threading.Event()
        self._last_frame_at = None
        self._status = "starting"

        self._thread = threading.Thread(
            target=self._run,
            name="stream-producer",
        )

    def _run(self):
        frames_read = 0

        try:
            fps = self._source.get(cv2.CAP_PROP_FPS)

            if fps <= 0:
                fps = 30.0

            frame_interval = 1.0 / fps
            next_frame_time = time.monotonic()

            print(f"Producer: source FPS = {fps:.2f}")

            while not self._stop_event.is_set():
                success, frame = self._source.read()

                if not success:
                    print("Producer: source.read() returned False")
                    break

                frames_read += 1
                self._last_frame_at = time.time()
                self._status = "running"

                self._buffer.put(frame)

                # Keep file playback close to its original frame rate.
                next_frame_time += frame_interval
                delay = next_frame_time - time.monotonic()

                if delay > 0:
                    if self._stop_event.wait(delay):
                        break
                else:
                    # Do not try to catch up by reading frames in a burst.
                    next_frame_time = time.monotonic()

        finally:
            print(f"Producer: total frames read = {frames_read}")
            print("Producer: closing buffer now")

            if self._status != "stopped":
                self._status = "stopped"

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

    def get_health(self):
        return {
            "status": self._status,
            "last_frame_at": self._last_frame_at,
        }
