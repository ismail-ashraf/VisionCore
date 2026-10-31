import gc
import time
from pathlib import Path
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from vision_core.core.config import (
    YOLO_MODEL_WEIGHTS,
    YOLO_MODEL_WEIGHTS_ONNX,
    CONFIDENCE_THRESHOLD,
)


# ---------------- CONFIGURATION ----------------

VIDEO_PATH = Path(
    r"C:\Users\iismmail\Downloads\Pothole video.mp4"
)

IMAGE_SIZE = 640
BATCH_SIZES = [1, 2, 4]

WARMUP_RUNS = 5
BENCHMARK_RUNS = 30

DEVICE = 0  # RTX 2050


# ---------------- LOAD TEST FRAMES ----------------

def load_frames(video_path, count=4):

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    frames = []

    while len(frames) < count:
        ret, frame = cap.read()

        if not ret:
            break

        frames.append(frame)

    cap.release()

    if len(frames) < count:
        raise RuntimeError(
            f"Expected {count} frames, got {len(frames)}"
        )

    return frames


# ---------------- GPU SYNCHRONIZATION ----------------

def synchronize_gpu():

    if torch.cuda.is_available():
        torch.cuda.synchronize(DEVICE)


# ---------------- BENCHMARK ----------------

def benchmark_model(model_path, backend, frames):

    print(f"\n{'=' * 55}")
    print(f"Benchmarking: {backend}")
    print(f"Model: {model_path}")
    print("=" * 55)

    model = YOLO(str(model_path))

    results_summary = {}

    for batch_size in BATCH_SIZES:

        batch_frames = frames[:batch_size]

        # Warmup
        for _ in range(WARMUP_RUNS):

            model.predict(
                source=batch_frames,
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                device=DEVICE,
                batch=batch_size,
                verbose=False,
                save=False,
            )

        synchronize_gpu()

        latencies = []

        # Actual benchmark
        for _ in range(BENCHMARK_RUNS):

            synchronize_gpu()

            start = time.perf_counter()

            predictions = model.predict(
                source=batch_frames,
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                device=DEVICE,
                batch=batch_size,
                verbose=False,
                save=False,
            )

            synchronize_gpu()

            elapsed = time.perf_counter() - start

            latencies.append(elapsed * 1000)

        avg_latency = np.mean(latencies)
        p50_latency = np.percentile(latencies, 50)
        p95_latency = np.percentile(latencies, 95)

        throughput = (
            batch_size / (avg_latency / 1000)
        )

        results_summary[batch_size] = {
            "avg_latency": avg_latency,
            "p50_latency": p50_latency,
            "p95_latency": p95_latency,
            "throughput": throughput,
        }

        print(f"\nBatch Size: {batch_size}")
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"P50 Latency:     {p50_latency:.2f} ms")
        print(f"P95 Latency:     {p95_latency:.2f} ms")
        print(f"Throughput:      {throughput:.2f} FPS")

        del predictions

    del model
    gc.collect()
    torch.cuda.empty_cache()

    return results_summary


# ---------------- MAIN ----------------

def main():

    if not Path(YOLO_MODEL_WEIGHTS).exists():
        raise FileNotFoundError(YOLO_MODEL_WEIGHTS)

    if not Path(YOLO_MODEL_WEIGHTS_ONNX).exists():
        raise FileNotFoundError(YOLO_MODEL_WEIGHTS_ONNX)

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available!")

    print("GPU:", torch.cuda.get_device_name(DEVICE))
    print("Image Size:", IMAGE_SIZE)
    print("Warmup Runs:", WARMUP_RUNS)
    print("Benchmark Runs:", BENCHMARK_RUNS)

    frames = load_frames(VIDEO_PATH)

    # Run PyTorch first
    pytorch_results = benchmark_model(
        YOLO_MODEL_WEIGHTS,
        "PyTorch",
        frames,
    )

    # Run ONNX after releasing PyTorch model
    onnx_results = benchmark_model(
        YOLO_MODEL_WEIGHTS_ONNX,
        "ONNX",
        frames,
    )

    # ---------------- COMPARISON ----------------

    print("\n\n========== FINAL COMPARISON ==========")

    print(
        f"{'Batch':<10}"
        f"{'PT Latency':<18}"
        f"{'ONNX Latency':<18}"
        f"{'PT FPS':<15}"
        f"{'ONNX FPS':<15}"
    )

    for batch_size in BATCH_SIZES:

        pt = pytorch_results[batch_size]
        onnx = onnx_results[batch_size]

        print(
            f"{batch_size:<10}"
            f"{pt['avg_latency']:<18.2f}"
            f"{onnx['avg_latency']:<18.2f}"
            f"{pt['throughput']:<15.2f}"
            f"{onnx['throughput']:<15.2f}"
        )

    print("\nBenchmark completed!")


if __name__ == "__main__":
    main()
