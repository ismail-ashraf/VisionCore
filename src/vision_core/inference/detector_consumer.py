from .anomaly_detector import detect_anomaly
from .preprocessor import preprocess_image


class AnomalyDetector:
    def __init__(self,model,category,memory_banks,thresholds):
        self.model = model
        self.category = category
        self.memory_banks = memory_banks
        self.thresholds = thresholds
        self.device = 'cpu'


    def predict(self,frame):
        image = preprocess_image(frame)

        image = image.to(self.device)

        prediction,score = detect_anomaly(
            model= self.model,
            memory_banks=self.memory_banks,
            thresholds=self.thresholds,
            category=self.category,
            image=image,
            device=self.device
        )

        return prediction,score
