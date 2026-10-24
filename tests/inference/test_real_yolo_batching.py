import time
import cv2
import pytest
from ultralytics import YOLO

from vision_core.core.config import (
    YOLO_MODEL_WEIGHTS,
    CONFIDENCE_THRESHOLD,
    DEVICE,
)
from vision_core.detection.detector import YOLODetector
from vision_core.inference.dynamic_batcher import DynamicBatcher


VIDEO_PATHS = [
    r"C:\Users\iismmail\Downloads\Pothole video.mp4",
    r"C:\Users\iismmail\Downloads\Pothole video.mp4",
    r"C:\Users\iismmail\Downloads\Pothole video.mp4",
]


def load_video_frames():
    frames = []

    for path in VIDEO_PATHS:
        source = cv2.VideoCapture(path)

        try:
            if not source.isOpened():
                pytest.fail(f"Could not open video: {path}")

            success, frame = source.read()

            if not success:
                pytest.fail(f"Could not read frame from: {path}")

            frames.append(frame)

        finally:
            source.release()

    return frames


def test_real_yolo_dynamic_batching():
    frames = load_video_frames()

    # Load YOLO only once.
    model = YOLO(YOLO_MODEL_WEIGHTS)

    detector = YOLODetector(
        model=model,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        device=DEVICE,
    )

    # Warm up the model before measuring inference.
    detector.predict(frames[0])

    # Benchmark individual inference.
    start = time.perf_counter()

    individual_results = [
        detector.predict(frame)
        for frame in frames
    ]

    individual_time = time.perf_counter() - start

    # Benchmark batch inference.
    start = time.perf_counter()

    batch_results = detector.predict_batch(frames)

    batch_time = time.perf_counter() - start

    assert len(individual_results) == len(frames)
    assert len(batch_results) == len(frames)

    print("\n========== REAL YOLO BENCHMARK ==========")
    print(f"Device: {DEVICE}")
    print(f"Frames: {len(frames)}")
    print(f"Individual inference: {individual_time:.4f} seconds")
    print(f"Batch inference:      {batch_time:.4f} seconds")

    if batch_time > 0:
        print(
            f"Speedup: {individual_time / batch_time:.2f}x"
        )

    print("=========================================")

    # Verify the actual DynamicBatcher with YOLO.
    batcher = DynamicBatcher(
        detector=detector,
        max_batch_size=4,
        max_wait_ms=30,
    )

    try:
        # Queue the requests before starting the worker so this test
        # deterministically exercises one batch of three frames.
        futures = [
            batcher.submit(frame)
            for frame in frames
        ]

        batcher.start()

        results = [
            future.result(timeout=60)
            for future in futures
        ]

        assert len(results) == len(frames)
        assert all(result is not None for result in results)

        print("\nDynamicBatcher + real YOLO: PASSED")
        print(f"Frames processed: {len(results)}")

    finally:
        batcher.stop()