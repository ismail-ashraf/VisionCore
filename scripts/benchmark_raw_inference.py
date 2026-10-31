
import gc
import time
import numpy as np
import torch
import onnxruntime as ort
from ultralytics import YOLO

from vision_core.core.config import (
    YOLO_MODEL_WEIGHTS,
    YOLO_MODEL_WEIGHTS_ONNX,
)


# ---------------- CONFIGURATION ----------------

DEVICE = "cuda:0"

IMAGE_SIZE = 640
BATCH_SIZES = [1, 2, 4]

WARMUP_RUNS = 10
BENCHMARK_RUNS = 100


# ---------------- PYTORCH BENCHMARK ----------------

def benchmark_pytorch(model, batch_size):

    # Identical input shape for both backends
    images = torch.rand(
        batch_size,
        3,
        IMAGE_SIZE,
        IMAGE_SIZE,
        device=DEVICE,
    )

    latencies = []

    # Warmup
    with torch.inference_mode():
        for _ in range(WARMUP_RUNS):
            model(images)

    torch.cuda.synchronize()

    # Benchmark
    with torch.inference_mode():

        for _ in range(BENCHMARK_RUNS):

            torch.cuda.synchronize()
            start = time.perf_counter()

            output = model(images)

            torch.cuda.synchronize()
            elapsed = time.perf_counter() - start

            latencies.append(elapsed * 1000)

    del images, output

    return calculate_metrics(latencies, batch_size)


# ---------------- ONNX BENCHMARK ----------------

def benchmark_onnx(session, input_name, batch_size):

    images = np.random.rand(
        batch_size,
        3,
        IMAGE_SIZE,
        IMAGE_SIZE,
    ).astype(np.float32)

    latencies = []

    # Warmup
    for _ in range(WARMUP_RUNS):
        session.run(None, {input_name: images})

    # Benchmark
    for _ in range(BENCHMARK_RUNS):

        start = time.perf_counter()

        output = session.run(
            None,
            {input_name: images},
        )

        elapsed = time.perf_counter() - start

        latencies.append(elapsed * 1000)

    del images, output

    return calculate_metrics(latencies, batch_size)


# ---------------- METRICS ----------------

def calculate_metrics(latencies, batch_size):

    avg_latency = np.mean(latencies)

    return {
        "avg_latency": avg_latency,
        "p50": np.percentile(latencies, 50),
        "p95": np.percentile(latencies, 95),
        "throughput": batch_size / (avg_latency / 1000),
    }


def print_metrics(name, metrics):

    print(f"\n{name}")
    print(f"Average Latency: {metrics['avg_latency']:.2f} ms")
    print(f"P50 Latency:     {metrics['p50']:.2f} ms")
    print(f"P95 Latency:     {metrics['p95']:.2f} ms")
    print(f"Throughput:      {metrics['throughput']:.2f} FPS")


# ---------------- MAIN ----------------

def main():

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available!")

    print("GPU:", torch.cuda.get_device_name(0))
    print("ONNX Runtime:", ort.__version__)

    # Load PyTorch model
    pytorch_yolo = YOLO(YOLO_MODEL_WEIGHTS)
    pytorch_model = pytorch_yolo.model.to(DEVICE).eval()

    # Load ONNX Runtime session
    ort.preload_dlls()

    options = ort.SessionOptions()

    session = ort.InferenceSession(
        YOLO_MODEL_WEIGHTS_ONNX,
        sess_options=options,
        providers=[
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ],
    )

    input_name = session.get_inputs()[0].name

    print("ONNX Providers:", session.get_providers())

    # Compare
    print("\n========== RAW INFERENCE BENCHMARK ==========")

    for batch_size in BATCH_SIZES:

        print(f"\n{'=' * 45}")
        print(f"BATCH SIZE: {batch_size}")
        print("=" * 45)

        pytorch_result = benchmark_pytorch(
            pytorch_model,
            batch_size,
        )

        onnx_result = benchmark_onnx(
            session,
            input_name,
            batch_size,
        )

        print_metrics("PyTorch", pytorch_result)
        print_metrics("ONNX", onnx_result)

        speed_difference = (
            (onnx_result["avg_latency"] /
             pytorch_result["avg_latency"]) - 1
        ) * 100

        if speed_difference > 0:
            print(
                f"\nONNX is {speed_difference:.2f}% slower"
            )
        else:
            print(
                f"\nONNX is {abs(speed_difference):.2f}% faster"
            )

    del pytorch_model, pytorch_yolo, session

    gc.collect()
    torch.cuda.empty_cache()

    print("\nBenchmark completed!")


if __name__ == "__main__":
    main()
