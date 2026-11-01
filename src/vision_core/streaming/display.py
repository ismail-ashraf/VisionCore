import threading


class DisplayManager:
    def __init__(self):
        self._frames = {}
        self._lock = threading.Lock()

    def update(self, camera_id, frame):
        with self._lock:
            self._frames[camera_id] = frame.copy()

    def get_frame(self, camera_id):
        with self._lock:
            frame = self._frames.get(camera_id)

            if frame is None:
                return None

            return frame.copy()

    def remove(self, camera_id):
        with self._lock:
            self._frames.pop(camera_id, None)