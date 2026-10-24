
from vision_core.inference.dynamic_batcher import DynamicBatcher


class FakeDetector:
    def __init__(self):
        self.batch_calls = []

    def predict_batch(self, frames):
        self.batch_calls.append(frames.copy())

        batch_detections = []

        for frame in frames:
            detections = [f"detections_for_{frame}"]
            batch_detections.append(detections)

        return batch_detections


def main():
    detector = FakeDetector()

    batcher = DynamicBatcher(
        detector=detector,
        max_batch_size=3,
        max_wait_ms=100
    )

    batcher.start()

    try:
        future_a = batcher.submit("frame_A")
        future_b = batcher.submit("frame_B")
        future_c = batcher.submit("frame_C")

        result_a = future_a.result(timeout=5)
        result_b = future_b.result(timeout=5)
        result_c = future_c.result(timeout=5)

        assert result_a == ["detections_for_frame_A"]
        assert result_b == ["detections_for_frame_B"]
        assert result_c == ["detections_for_frame_C"]

        print("Future A:", result_a)
        print("Future B:", result_b)
        print("Future C:", result_c)

        assert len(detector.batch_calls) == 1
        assert detector.batch_calls[0] == [
            "frame_A",
            "frame_B",
            "frame_C"
        ]

        print("Batch inference test passed!")
        print("Number of inference calls:", len(detector.batch_calls))
        print("Frames in the batch:", detector.batch_calls[0])

    finally:
        batcher.stop()

    assert not batcher.worker_thread.is_alive()
    print("Worker shutdown test passed!")


if __name__ == "__main__":
    main()
