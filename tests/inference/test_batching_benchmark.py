import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import pytest
import torch
from ultralytics import YOLO

from vision_core.core.config import (
    YOLO_MODEL_WEIGHTS,
    CONFIDENCE_THRESHOLD,
    DEVICE,
)
from vision_core.detection.detector import YOLODetector
from vision_core.inference.dynamic_batcher import DynamicBatcher


VIDEO_PATH = r"C:\Users\iismmail\Downloads\Pothole video.mp4"

BATCH_SIZES = [1, 2, 4, 8]
REPEATS = 3


def synchronize_device():
    if str(DEVICE).startswith("cuda") and torch.cuda.is_available():
        torch.cuda.synchronize()


def load_frames(count=8):
    source = cv2.VideoCapture(VIDEO_PATH)

    if not source.isOpened():
        pytest.fail(f"Could not open video: {VIDEO_PATH}")

    frames = []

    try:
        while len(frames) < count:
            success, frame = source.read()

            if not success:
                break

            frames.append(frame)
    finally:
        source.release()

    if len(frames) < count:
        pytest.fail(
            f"Expected {count} frames, but read {len(frames)}"
        )

    return frames


def test_batching_performance():
    frames = load_frames(8)

    model = YOLO(YOLO_MODEL_WEIGHTS)

    detector = YOLODetector(
        model=model,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        device=DEVICE,
    )

    # Warm-up.
    detector.predict(frames[0])
    detector.predict_batch(frames[:2])
    synchronize_device()

    print("\n========== DIRECT INFERENCE BENCHMARK ==========")
    print(f"Device: {DEVICE}")
    print(f"Frames per experiment: {len(frames)}")
    print(f"Repeats: {REPEATS}\n")

    # Baseline: individual inference.
    baseline_times = []

    for _ in range(REPEATS):
        synchronize_device()
        start = time.perf_counter()

        results = [
            detector.predict(frame)
            for frame in frames
        ]

        synchronize_device()
        baseline_times.append(time.perf_counter() - start)

        assert len(results) == len(frames)

    baseline_time = sum(baseline_times) / REPEATS
    baseline_fps = len(frames) / baseline_time

    print(
        f"Individual: total={baseline_time:.4f}s | "
        f"throughput={baseline_fps:.2f} frames/s"
    )

    # Compare batch sizes using the same eight frames.
    for batch_size in BATCH_SIZES:
        total_times = []

        for _ in range(REPEATS):
            synchronize_device()
            start = time.perf_counter()

            batch_results = []

            for offset in range(0, len(frames), batch_size):
                batch = frames[offset:offset + batch_size]
                batch_results.extend(detector.predict_batch(batch))

            synchronize_device()
            total_times.append(time.perf_counter() - start)

            assert len(batch_results) == len(frames)

        avg_total = sum(total_times) / REPEATS
        throughput = len(frames) / avg_total
        avg_frame_time_ms = avg_total / len(frames) * 1000
        speedup = baseline_time / avg_total

        print(
            f"Batch size={batch_size} | "
            f"total={avg_total:.4f}s | "
            f"throughput={throughput:.2f} frames/s | "
            f"avg/frame={avg_frame_time_ms:.2f}ms | "
            f"speedup={speedup:.2f}x"
        )

    print("\n========== DYNAMIC BATCHER BENCHMARK ==========")

    # Record the actual batch sizes used by the shared worker.
    actual_batch_sizes = []
    batch_sizes_lock = threading.Lock()

    original_predict_batch = detector.predict_batch

    def measured_predict_batch(batch_frames):
        with batch_sizes_lock:
            actual_batch_sizes.append(len(batch_frames))

        return original_predict_batch(batch_frames)

    detector.predict_batch = measured_predict_batch

    batcher = DynamicBatcher(
        detector=detector,
        max_batch_size=4,
        max_wait_ms=30,
    )

    batcher.start()

    try:
        def submit_frame(frame):
            start = time.perf_counter()

            future = batcher.submit(frame)
            detections = future.result(timeout=120)

            latency = time.perf_counter() - start

            return latency, detections

        synchronize_device()
        start = time.perf_counter()

        # Eight simultaneous requests sharing one batcher.
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(submit_frame, frame)
                for frame in frames
            ]

            results = [
                future.result(timeout=180)
                for future in futures
            ]

        synchronize_device()
        total_time = time.perf_counter() - start

        latencies = [latency for latency, _ in results]
        throughput = len(results) / total_time

        assert len(results) == len(frames)

        print(f"Requests processed: {len(results)}")
        print(f"Actual batch sizes: {actual_batch_sizes}")
        print(f"Total time: {total_time:.4f}s")
        print(f"Throughput: {throughput:.2f} frames/s")
        print(
            f"Average latency: "
            f"{sum(latencies) / len(latencies) * 1000:.2f}ms"
        )
        print(f"Max latency: {max(latencies) * 1000:.2f}ms")

    finally:
        batcher.stop()
        detector.predict_batch = original_predict_batch

    print("===============================================\n")