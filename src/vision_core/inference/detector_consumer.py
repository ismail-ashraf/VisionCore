from .anomaly_detector import detect_anomaly
from .preprocessor import preprocess_image
from vision_core.core.config import DEVICE


class AnomalyDetector:
    def __init__(self,model,memory_banks,thresholds):
        self.model = model
        self.memory_banks = memory_banks
        self.thresholds = thresholds
        self.device = DEVICE


    def predict(self,frame,category):
        image = preprocess_image(frame)

        image = image.to(self.device)

        prediction,score = detect_anomaly(
            model= self.model,
            memory_banks=self.memory_banks,
            thresholds=self.thresholds,
            category=category,
            image=image,
            device=self.device
        )

        return prediction,score
