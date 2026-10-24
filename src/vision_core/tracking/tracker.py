import numpy as np
from vision_core.tracking.kalman_filter import KalmanFilter

class Track:
    def __init__(self, track_id, bbox, initial_position):
        self.track_id = track_id
        self.bbox = bbox
        self.kalman_filter = KalmanFilter(
            initial_position=initial_position
        )

    def predict(self):
        return self.kalman_filter.predict()

    def update(self, measurement):
        return self.kalman_filter.update(measurement)


class Tracker:
    def __init__(self, max_distance=80.0):
        self.tracks = {}
        self.next_id = 1
        self.max_distance = max_distance

    def create_track(self, detection):
        bbox = detection.bbox
        x1, y1, x2, y2 = bbox

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        initial_position = (cx, cy)

        track = Track(
            self.next_id,
            bbox,
            initial_position
        )

        self.tracks[self.next_id] = track
        self.next_id += 1

        return track

    def update(self, detections):

        # 1. Predict the position of every existing track
        predicted_positions = {}

        for track_id, track in self.tracks.items():
            predicted_state = track.predict()
            state = np.asarray(predicted_state).reshape(-1)

            predicted_positions[track_id] = (
                float(state[0]),
                float(state[1])
            )

        # Each existing track can match only one detection
        unmatched_track_ids = set(self.tracks.keys())

        # 2. Match each detection to the nearest available track
        for detection in detections:
            bbox = detection.bbox
            x1, y1, x2, y2 = bbox

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
                    cy - predicted_cy
                )

                if distance < best_distance:
                    best_distance = distance
                    best_track_id = track_id

            # 3. If no suitable track exists, create a new one
            if best_track_id is None:
                self.create_track(detection)

            else:
                # 4. Correct the matched track using YOLO's measurement
                track = self.tracks[best_track_id]

                track.update(measurement)
                track.bbox = bbox

                unmatched_track_ids.remove(best_track_id)

        # 5. Return all currently stored tracks
        return list(self.tracks.values())