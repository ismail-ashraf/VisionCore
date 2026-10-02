from contextlib import asynccontextmanager
import cv2
from fastapi import FastAPI
from vision_core.detection.detector import YOLODetector
from ultralytics import YOLO
from vision_core.core.config import YOLO_MODEL_WEIGHTS,CONFIDENCE_THRESHOLD,DEVICE,VISIONCORE_MODEL_PATH,VISIONCORE_MEMORY_BANK_PATH
from vision_core.inference.detector_consumer import AnomalyDetector
from vision_core.inference.anomaly_detector import load_anomaly_detector
from vision_core.inference.model import load_model
from vision_core.streaming.buffer import StreamingBuffer
from vision_core.streaming.consumer import StreamConsumer
from vision_core.streaming.producer import StreamProducer

@asynccontextmanager
async def lifespan(_:FastAPI):
    #load anomaly model
    anomaly_model = load_model(
        VISIONCORE_MODEL_PATH
    )

    #load anomaly data
    memory_banks,thresholds,supported_categories = load_anomaly_detector(
        VISIONCORE_MEMORY_BANK_PATH
    )

    anomaly_detector = AnomalyDetector(
        model=anomaly_model,
        memory_banks=memory_banks,
        thresholds=thresholds
    )

    #load yolo
    yolo_model = YOLO(
        YOLO_MODEL_WEIGHTS
    )

    yolo_detector = YOLODetector(
        model=yolo_model,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        device=DEVICE
    )

    #buffer
    buffer = StreamingBuffer()

    #video source
    source = cv2.VideoCapture(0)

    if not source.isOpened():
        raise RuntimeError(
            "Could Not Open Video Source"
        )

    #producer
    producer = StreamProducer(
        source=source,
        buffer=buffer
    )

    #consumer
    consumer = StreamConsumer(
        buffer=buffer,
        anomaly_detector=anomaly_detector,
        yolo_detector=yolo_detector
    )

    producer.start()
    consumer.start()

    yield

    consumer.stop()
    producer.stop()
    source.release()


app = FastAPI(lifespan=lifespan)
