from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from vision_core.core.config import CONFIDENCE_THRESHOLD,DEVICE,YOLO_MODEL_WEIGHTS
from vision_core.core.system_logger import configure_system_logger
from vision_core.detection.detector import YOLODetector
from vision_core.inference.dynamic_batcher import DynamicBatcher
from vision_core.streaming.display import DisplayManager
from vision_core.streaming.manager import StreamManager
from vision_core.storage.database import Database
from vision_core.analytics.collector import MetricsCollector
from vision_core.api.routes.camera import router as camera_router
from vision_core.api.routes.monitoring import router as monitoring_router
from vision_core.api.routes.analytics import router as analytics_router
from vision_core.api.routes.logs import router as logs_router
from vision_core.core.runtime_settings import RuntimeSettings
from vision_core.api.routes.settings import router as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App Started")

    collector = None
    batcher = None
    stream_manager = None
    system_logger = None

    try:
        # 1. Initialize database
        database = Database()
        database.initialize()

        # 2. Configure system logger
        system_logger = configure_system_logger(database)

        app.state.database = database
        app.state.system_logger = system_logger

        system_logger.info(
            "VisionCore application started",
            extra={"event": "APPLICATION_STARTED"},
        )

        # 3. Load YOLO model
        yolo_model = YOLO(YOLO_MODEL_WEIGHTS)

        yolo_detector = YOLODetector(
            model=yolo_model,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            device=DEVICE,
        )

        # 4. Initialize dynamic batcher
        batcher = DynamicBatcher(
            detector=yolo_detector,
            max_batch_size=4,
            max_wait_ms=15,
        )

        batcher.start()

        # 5. Initialize display manager
        display_manager = DisplayManager()

        # 6. Initialize stream manager
        stream_manager = StreamManager(
            batcher=batcher,
            display_manager=display_manager,
            logger=system_logger,
        )

        app.state.stream_manager = stream_manager

        # 7. Start metrics collector
        collector = MetricsCollector(
            stream_manager=stream_manager,
            database=database,
            interval=10,
        )

        collector.start()

        runtime_settings = RuntimeSettings(
            detector=yolo_detector,
            batcher=batcher,
            stream_manager=stream_manager,
            collector=collector,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            device=DEVICE,
            max_batch_size=4,
            max_wait_ms=15,
            metrics_interval=10,
            drift_window_size=1000,
            drift_monitor_interval=30,
        )

        app.state.runtime_settings = runtime_settings

        yield

    except Exception:
        if system_logger is not None:
            system_logger.exception(
                "VisionCore application startup failed",
                extra={"event": "APPLICATION_STARTUP_FAILED"},
            )
        raise

    finally:
        # 8. Stop metrics collector
        if collector is not None:
            collector.stop()

        # 9. Stop all cameras
        if stream_manager is not None:
            try:
                stream_manager.stop_all()
            except Exception:
                if system_logger is not None:
                    system_logger.exception(
                        "Error while stopping StreamManager",
                        extra={"event": "STREAM_MANAGER_SHUTDOWN_FAILED"},
                    )
                else:
                    print("StreamManager shutdown error")

        # 10. Stop batcher
        if batcher is not None:
            batcher.stop()

        # 11. Log application shutdown
        if system_logger is not None:
            system_logger.info(
                "VisionCore application stopped",
                extra={"event": "APPLICATION_STOPPED"},
            )

        print("App Ended")


app = FastAPI(
    title="VisionCore API",
    lifespan=lifespan,
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routes
app.include_router(camera_router)
app.include_router(monitoring_router)
app.include_router(analytics_router)
app.include_router(logs_router)
app.include_router(settings_router)
