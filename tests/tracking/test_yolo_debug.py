
import cv2
from ultralytics import YOLO

from vision_core.core.config import YOLO_MODEL_WEIGHTS

VIDEO_PATH = (
    r"C:\Users\iismmail\Downloads"
    r"\pcb Assembly Channel line.mp4"
)


def test_yolo_predictions_debug():
    model = YOLO(YOLO_MODEL_WEIGHTS)

    print("\nMODEL WEIGHTS:", YOLO_MODEL_WEIGHTS)
    print("MODEL TASK:", model.task)
    print("MODEL CLASSES:", model.names)

    source = cv2.VideoCapture(VIDEO_PATH)
    assert source.isOpened(), f"Cannot open video: {VIDEO_PATH}"

    try:
        for frame_number in range(5):
            success, frame = source.read()

            if not success:
                print("Video ended before 5 frames.")
                break

            results = model.predict(
                frame,
                conf=0.25,
                verbose=False,
            )

            result = results[0]

            print(f"\nFRAME {frame_number + 1}")

            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = float(box.conf.item())
                class_name = model.names[class_id]

                print(
                    f"class={class_name}, "
                    f"id={class_id}, "
                    f"confidence={confidence:.3f}"
                )

            annotated = result.plot()

            cv2.imshow("YOLO Debug", annotated)

            if cv2.waitKey(500) & 0xFF == ord("q"):
                break

    finally:
        source.release()
        cv2.destroyAllWindows()
