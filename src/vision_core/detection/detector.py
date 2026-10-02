import cv2
import torch
from vision_core.detection.schema import Detection


class YOLODetector:
    def __init__(self,model,device , confidence_threshold = 0.5):
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.device = device

    def predict(self,frame):
        if frame is None:
            raise ValueError(
                "Input frame is None"
            )

        try:
            with torch.inference_mode():
                result = self.model.predict(
                    frame,
                    conf=self.confidence_threshold,
                    device=self.device
                )

                detections = []

                for i in range(len(result[0].boxes.xyxy)):
                    bbox = result[0].boxes.xyxy[i].tolist()
                    class_id = int(result[0].boxes.cls[i])
                    confidence = float(result[0].boxes.conf[i])
                    class_name = str(result[0].names[int(class_id)])

                    detections.append(
                        Detection(
                            bbox=bbox,
                            class_id=class_id,
                            confidence=confidence,
                            class_name=class_name
                        )
                    )

            return detections


        except Exception as e:
            raise RuntimeError(
                "YOLO inference failed"
            ) from e


    @staticmethod
    def draw_detections(frame,detections):

        for detection in detections:
            bbox = detection.bbox
            x1,y1,x2,y2 = map(int,bbox)

            class_name = detection.class_name
            confidence = detection.confidence

            cv2.rectangle(
                img=frame,
                pt1=(x1,y1),
                pt2=(x2,y2),
                color=(0,255,0),
                thickness=2
            )

            cv2.putText(
                img=frame,
                text=f"{class_name} {confidence:.2f}",
                org=(x1,y1 - 10),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.8,
                color=(0, 255, 0),
                thickness=2
            )

        return frame


