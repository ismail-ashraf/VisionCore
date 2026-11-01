import threading
import logging
from collections import deque
import numpy as np
from vision_core.monitoring.feature_extractor import FeatureExtractor


logger = logging.getLogger(__name__)


class DriftMonitor:

    EPSILON = 0.0001

    REFERENCE = {
        "brightness": {
            "bins": [-np.inf, 51, 102, 153, 204, np.inf],
            "distribution": [
                0.009335, 0.301050, 0.639440, 0.050175, 0.0
            ],
        },
        "contrast": {
            "bins": [-np.inf, 20, 40, 60, 80, np.inf],
            "distribution": [
                0.001167, 0.109685, 0.606768, 0.274212, 0.008168
            ],
        },
        "sharpness": {
            "bins": [
                -np.inf, 240.56018844, 360.87759248,
                545.33115361, 1001.51578907, np.inf
            ],
            "distribution": [
                0.200700, 0.199533, 0.199533, 0.199533, 0.200700
            ],
        },
    }

    def __init__(self, window_size=1000, monitor_interval=30):
        self._extractor = FeatureExtractor()

        self._features = deque(maxlen=window_size)
        self._window_size = window_size
        self._monitor_interval = monitor_interval

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._monitor_thread = None
        self._latest_report = None

    def update(self, frame):
        features = self._extractor.extract(frame)

        with self._lock:
            self._features.append(features)

    def get_features(self):
        with self._lock:
            return list(self._features)

    @property
    def sample_count(self):
        with self._lock:
            return len(self._features)

    def get_latest_report(self):
        with self._lock:
            if self._latest_report is None:
                return None

            return {
                "sample_count": self._latest_report["sample_count"],
                "features": {
                    name: result.copy()
                    for name, result in self._latest_report["features"].items()
                },
            }

    @classmethod
    def _smooth_distribution(cls, distribution):
        distribution = np.asarray(distribution, dtype=np.float64)
        distribution += cls.EPSILON

        return distribution / distribution.sum()

    @classmethod
    def _calculate_psi(cls, expected, actual):
        expected = cls._smooth_distribution(expected)
        actual = cls._smooth_distribution(actual)

        psi = (actual - expected) * np.log(actual / expected)

        return float(np.sum(psi))

    def calculate_report(self):

        with self._lock:
            if len(self._features) < self._window_size:
                return None

            features = list(self._features)

        report = {
            "sample_count": len(features),
            "features": {},
        }

        for feature_name, reference in self.REFERENCE.items():

            values = [
                sample[feature_name]
                for sample in features
            ]

            counts, _ = np.histogram(
                values,
                bins=reference["bins"],
            )

            actual_distribution = counts / counts.sum()

            psi = self._calculate_psi(
                expected=reference["distribution"],
                actual=actual_distribution,
            )

            if psi < 0.1:
                status = "low"
            elif psi < 0.25:
                status = "moderate"
            else:
                status = "high"

            report["features"][feature_name] = {
                "psi": psi,
                "status": status,
            }

        return report

    def _monitor_loop(self):

        while not self._stop_event.wait(self._monitor_interval):

            report = self.calculate_report()

            if report is None:
                continue

            with self._lock:
                self._latest_report = report

            logger.info("Drift report: %s", report)

    def start(self):

        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="drift-monitor",
            daemon=True,
        )

        self._monitor_thread.start()

    def stop(self):

        self._stop_event.set()

        if (
            self._monitor_thread is not None
            and self._monitor_thread.is_alive()
        ):
            self._monitor_thread.join()

    @property
    def window_size(self):
        return self._window_size
