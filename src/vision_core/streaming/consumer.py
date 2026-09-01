import threading
from .buffer import _STOP,StreamingBuffer
from vision_core.inference.detector_consumer import AnomalyDetector


class StreamConsumer:
    def __init__(self , buffer:StreamingBuffer,detector:AnomalyDetector):
        self._buffer = buffer
        self._detector = detector
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="stream-consumer"
        )

    def _run(self):
        while not self._stop_event.is_set():

            frame = self._buffer.get_latest()

            if frame is _STOP:
                break

            prediction,score = self._detector.predict(frame)

            print(
                f"Prediction : {prediction}"
                f"Score : {score}"
            )

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._buffer.stop_consumer()
        self._thread.join()