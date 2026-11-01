
import threading


class RuntimeSettings:
    def __init__(
        self,
        detector,
        batcher,
        stream_manager,
        collector,
        confidence_threshold=0.5,
        device="cpu",
        max_batch_size=4,
        max_wait_ms=15,
        metrics_interval=10,
        drift_window_size=1000,
        drift_monitor_interval=30,
    ):
        self.detector = detector
        self.batcher = batcher
        self.stream_manager = stream_manager
        self.collector = collector

        self._lock = threading.Lock()

        self._settings = {
            "confidence_threshold": confidence_threshold,
            "device": device,
            "max_batch_size": max_batch_size,
            "max_wait_ms": max_wait_ms,
            "metrics_interval": metrics_interval,
            "drift_window_size": drift_window_size,
            "drift_monitor_interval": drift_monitor_interval,
        }

    def get_settings(self):
        with self._lock:
            return {
                **self._settings,
                "device_change_supported": False,
            }

    def update_settings(self, **updates):
        allowed_settings = {
            "confidence_threshold",
            "max_batch_size",
            "max_wait_ms",
            "metrics_interval",
            "drift_window_size",
            "drift_monitor_interval",
        }

        unknown_settings = set(updates) - allowed_settings

        if unknown_settings:
            raise ValueError(
                f"Unsupported settings: {unknown_settings}"
            )

        if not updates:
            return self.get_settings()

        with self._lock:
            new_settings = {
                **self._settings,
                **updates,
            }

            # Validate all values before applying changes.
            self.detector._validate_confidence(
                new_settings["confidence_threshold"]
            )

            self.batcher._validate_settings(
                new_settings["max_batch_size"],
                new_settings["max_wait_ms"],
            )

            self.collector._validate_interval(
                new_settings["metrics_interval"]
            )

            # Update only the components whose settings changed.
            if (
                new_settings["confidence_threshold"]
                != self._settings["confidence_threshold"]
            ):
                self.detector.update_settings(
                    confidence_threshold=new_settings[
                        "confidence_threshold"
                    ]
                )

            if (
                new_settings["max_batch_size"]
                != self._settings["max_batch_size"]
                or new_settings["max_wait_ms"]
                != self._settings["max_wait_ms"]
            ):
                self.batcher.update_settings(
                    max_batch_size=new_settings["max_batch_size"],
                    max_wait_ms=new_settings["max_wait_ms"],
                )

            if (
                new_settings["metrics_interval"]
                != self._settings["metrics_interval"]
            ):
                self.collector.update_interval(
                    new_settings["metrics_interval"]
                )

            if (
                new_settings["drift_window_size"]
                != self._settings["drift_window_size"]
                or new_settings["drift_monitor_interval"]
                != self._settings["drift_monitor_interval"]
            ):
                self.stream_manager.update_drift_settings(
                    window_size=new_settings["drift_window_size"],
                    monitor_interval=new_settings[
                        "drift_monitor_interval"
                    ],
                )

            self._settings = new_settings

            return {
                **self._settings,
                "device_change_supported": False,
            }
