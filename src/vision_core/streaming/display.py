
import cv2
import threading


class DisplayManager:
    def __init__(self):
        self._frames = {}
        self._pending_closes = set()
        self._lock = threading.Lock()

    def update(self, camera_id, frame):
        with self._lock:
            self._frames[camera_id] = frame

    def run_once(self):
        self.show()
        cv2.waitKey(1)
        self.process_pending_closes()
        return self.get_closed_windows()

    def show(self):
        with self._lock:
            frames = self._frames.copy()

        for camera_id, frame in frames.items():
            window_name = f"VisionCore - {camera_id}"
            cv2.imshow(window_name, frame)

    def get_closed_windows(self):
        closed_cameras = []

        with self._lock:
            camera_ids = list(self._frames.keys())

        for camera_id in camera_ids:
            window_name = f"VisionCore - {camera_id}"

            try:
                visible = cv2.getWindowProperty(
                    window_name,
                    cv2.WND_PROP_VISIBLE,
                )

                if visible == 0:
                    closed_cameras.append(camera_id)

            except cv2.error as exc:
                print(f"Could not check {camera_id} window: {exc}")

        return closed_cameras

    def remove(self, camera_id):
        with self._lock:
            self._frames.pop(camera_id, None)
            self._pending_closes.add(camera_id)

    def process_pending_closes(self):
        with self._lock:
            camera_ids = list(self._pending_closes)
            self._pending_closes.clear()

        for camera_id in camera_ids:
            window_name = f"VisionCore - {camera_id}"

            try:
                cv2.destroyWindow(window_name)
                print(f"Display: closed {camera_id}")
            except cv2.error as exc:
                print(f"Could not close {camera_id}: {exc}")
