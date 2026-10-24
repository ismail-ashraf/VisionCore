
import numpy as np


class KalmanFilter:
    def __init__(self, initial_position):
        cx, cy = initial_position

        # State: [cx, cy, vx, vy]
        self.x = np.array([
            [cx],
            [cy],
            [0.0],
            [0.0]
        ])

        self.F = np.array([
            [1.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

        # Measurement: [cx, cy]
        self.H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ])

        # State uncertainty
        self.P = np.eye(4) * 10.0

        # Motion model uncertainty
        self.Q = np.eye(4) * 0.1

        # Measurement uncertainty
        self.R = np.eye(2) * 4.0

        self.I = np.eye(4)

    def predict(self):
        self.x = self.F @ self.x

        self.P = (
            self.F @ self.P @ self.F.T
            + self.Q
        )

        return self.x

    def update(self, measurement):
        z = np.asarray(
            measurement, dtype=float
        ).reshape(2, 1)

        # Innovation: measurement - predicted measurement
        y = z - self.H @ self.x

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman gain
        K = np.linalg.solve(
            S.T,
            (self.P @ self.H.T).T
        ).T

        # Correct state
        self.x = self.x + K @ y

        # Update uncertainty (Joseph form)
        A = self.I - K @ self.H
        self.P = (
            A @ self.P @ A.T
            + K @ self.R @ K.T
        )

        return self.x

# init_pos = (100,50)
# kalman = KalmanFilter(initial_position=init_pos)
#
# result = kalman.predict()
#
# print(result)
#
# update = kalman.update((103,51))
# print(update)