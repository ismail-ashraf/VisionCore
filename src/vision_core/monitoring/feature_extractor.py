import cv2
import numpy as np

class FeatureExtractor:

    @staticmethod
    def extract(frame: np.ndarray) -> dict[str, float]:

        if frame is None or frame.size == 0:
            raise ValueError("Input frame is empty")

        if frame.ndim == 2:
            gray = frame

        elif frame.ndim == 3 and frame.shape[2] == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        else:
            raise ValueError("Unsupported frame format")

        brightness = np.mean(gray)

        contrast = np.std(gray)

        laplacian = cv2.Laplacian(
            gray,
            cv2.CV_64F
        )

        sharpness = laplacian.var()

        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "sharpness": float(sharpness)
        }