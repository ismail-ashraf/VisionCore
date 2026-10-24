from contextlib import asynccontextmanager
import cv2
from fastapi import FastAPI
from ultralytics import YOLO
from vision_core.core.config import YOLO_MODEL_WEIGHTS,CONFIDENCE_THRESHOLD, DEVICE
from vision_core.detection.detector import YOLODetector
from vision_core.streaming.buffer import StreamingBuffer
from vision_core.streaming.consumer import StreamConsumer
from vision_core.streaming.producer import StreamProducer


@asynccontextmanager
async def lifespan(_: FastAPI):
    print("App Started")

    # Load YOLO model only
    yolo_model = YOLO(YOLO_MODEL_WEIGHTS)

    yolo_detector = YOLODetector(
        model=yolo_model,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        device=DEVICE,
    )

    # Initialize streaming buffer
    buffer = StreamingBuffer()

    # Open video source
    source = cv2.VideoCapture(
        r"C:\Users\iismmail\Downloads\Pothole video.mp4"
    )

    if not source.isOpened():
        raise RuntimeError("Could Not Open Video Source")

    # Initialize producer
    producer = StreamProducer(
        source=source,
        buffer=buffer,
    )

    # Initialize consumer
    consumer = StreamConsumer(
        buffer=buffer,
        yolo_detector=yolo_detector,
    )

    producer.start()
    consumer.start()

    try:
        yield
    finally:
        producer.stop()
        consumer.stop()
        source.release()
        print("App Ended")


app = FastAPI(lifespan=lifespan)
