from contextlib import asynccontextmanager
import cv2
from fastapi import FastAPI
from ultralytics import YOLO
from vision_core.core.config import YOLO_MODEL_WEIGHTS,CONFIDENCE_THRESHOLD,DEVICE
from vision_core.detection.detector import YOLODetector
from vision_core.inference.dynamic_batcher import DynamicBatcher
from vision_core.streaming.buffer import StreamingBuffer
from vision_core.streaming.consumer import StreamConsumer
from vision_core.streaming.producer import StreamProducer


@asynccontextmanager
async def lifespan(_: FastAPI):
    print("App Started")

    source = None
    producer = None
    consumer = None
    batcher = None

    try:
        yolo_model = YOLO(YOLO_MODEL_WEIGHTS)

        yolo_detector = YOLODetector(
            model=yolo_model,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            device=DEVICE,
        )

        batcher = DynamicBatcher(
            detector=yolo_detector,
            max_batch_size=4,
            max_wait_ms=15,
        )
        batcher.start()

        buffer = StreamingBuffer()

        source = cv2.VideoCapture(
            r"C:\Users\iismmail\Downloads\Pothole video.mp4"
        )

        if not source.isOpened():
            raise RuntimeError("Could Not Open Video Source")

        producer = StreamProducer(
            source=source,
            buffer=buffer,
        )

        consumer = StreamConsumer(
            buffer=buffer,
            batcher=batcher,
        )

        producer.start()
        consumer.start()

        yield

    finally:
        if producer is not None:
            producer.stop()

        if consumer is not None:
            consumer.stop()
        if batcher is not None:
            batcher.stop()

        if source is not None:
            source.release()

        cv2.destroyAllWindows()
        print("App Ended")


app = FastAPI(lifespan=lifespan)