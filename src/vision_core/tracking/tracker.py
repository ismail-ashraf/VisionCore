
import numpy as np
from vision_core.tracking.kalman_filter import KalmanFilter


class Track:
    def __init__(self, track_id, detection, initial_position):
        self.track_id = track_id
        self.bbox = detection.bbox
        self.class_id = detection.class_id
        self.class_name = detection.class_name
        self.confidence = detection.confidence

        self.kalman_filter = KalmanFilter(
            initial_position=initial_position
        )

        self.missed_frames = 0
        self.is_updated = True

    def predict(self):
        return self.kalman_filter.predict()

    def update(self, detection, measurement):
        self.kalman_filter.update(measurement)

        self.bbox = detection.bbox
        self.class_id = detection.class_id
        self.class_name = detection.class_name
        self.confidence = detection.confidence

        self.missed_frames = 0
        self.is_updated = True


class Tracker:
    def __init__(self, max_distance=80.0, max_missed_frames=2):
        self.tracks = {}
        self.next_id = 1
        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames

    def create_track(self, detection):
        x1, y1, x2, y2 = detection.bbox

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        track = Track(
            track_id=self.next_id,
            detection=detection,
            initial_position=(cx, cy),
        )

        self.tracks[self.next_id] = track
        self.next_id += 1

        return track

    def update(self, detections):
        # 1. Predict existing track positions
        predicted_positions = {}

        for track_id, track in self.tracks.items():
            predicted_state = track.predict()
            state = np.asarray(predicted_state).reshape(-1)

            predicted_positions[track_id] = (
                float(state[0]),
                float(state[1]),
            )

            track.is_updated = False

        # 2. Start with all existing tracks unmatched
        unmatched_track_ids = set(self.tracks.keys())

        # 3. Match detections to nearest available tracks
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox

            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            measurement = (cx, cy)

            best_track_id = None
            best_distance = self.max_distance

            for track_id in unmatched_track_ids:
                predicted_cx, predicted_cy = (
                    predicted_positions[track_id]
                )

                distance = np.hypot(
                    cx - predicted_cx,
                    cy - predicted_cy,
                )

                if distance < best_distance:
                    best_distance = distance
                    best_track_id = track_id

            if best_track_id is None:
                self.create_track(detection)

            else:
                track = self.tracks[best_track_id]
                track.update(detection, measurement)

                unmatched_track_ids.remove(best_track_id)

        # 4. Age unmatched tracks
        for track_id in unmatched_track_ids:
            self.tracks[track_id].missed_frames += 1

        # 5. Remove expired tracks
        expired_track_ids = [
            track_id
            for track_id, track in self.tracks.items()
            if track.missed_frames > self.max_missed_frames
        ]

        for track_id in expired_track_ids:
            del self.tracks[track_id]

        return list(self.tracks.values())
