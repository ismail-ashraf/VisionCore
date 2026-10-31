import asyncio
from contextlib import asynccontextmanager
import cv2
from fastapi import FastAPI
from ultralytics import YOLO
from vision_core.core.config import CONFIDENCE_THRESHOLD,DEVICE,YOLO_MODEL_WEIGHTS
from vision_core.detection.detector import YOLODetector
from vision_core.inference.dynamic_batcher import DynamicBatcher
from vision_core.streaming.display import DisplayManager
from vision_core.streaming.manager import StreamManager
from vision_core.api.routes.camera import router as camera_router


async def display_loop(stream_manager, display_manager):
    while True:
        display_manager.show()
        cv2.waitKey(1)
        display_manager.process_pending_closes()

        # closed_cameras = display_manager.get_closed_windows()
        #
        # for camera_id in closed_cameras:
        #     try:
        #         stream_manager.stop_camera(camera_id)
        #         print(f"Stopped camera: {camera_id}")
        #     except ValueError:
        #         pass

        await asyncio.sleep(0.01)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App Started")

    batcher = None
    stream_manager = None
    display_task = None

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

        display_manager = DisplayManager()

        stream_manager = StreamManager(
            batcher=batcher,
            display_manager=display_manager,
        )

        app.state.stream_manager = stream_manager

        # Run the display loop in the background
        display_task = asyncio.create_task(
            display_loop(
                stream_manager=stream_manager,
                display_manager=display_manager,
            )
        )

        yield

    finally:
        # Stop the display loop first
        if display_task is not None:
            display_task.cancel()

            try:
                await display_task
            except asyncio.CancelledError:
                pass

        # Stop all camera streams
        if stream_manager is not None:
            try:
                stream_manager.stop_all()
            except Exception as exc:
                print(f"StreamManager shutdown error: {exc}")

        # Stop the shared inference batcher
        if batcher is not None:
            batcher.stop()

        cv2.destroyAllWindows()

        print("App Ended")


app = FastAPI(lifespan=lifespan)
app.include_router(camera_router)