from ultralytics import YOLO
import cv2
import os


MODEL_PATH = "yolo26n.pt"
VIDEO_PATH = "data/videos/traffic.mp4"
OUTPUT_PATH = "outputs/videos/vehicle_detection.mp4"


def main():

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print("❌ Could not open video")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    os.makedirs("outputs/videos", exist_ok=True)

    writer = cv2.VideoWriter(
        OUTPUT_PATH,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    vehicle_classes = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        results = model(
            frame,
            conf=0.40,
            verbose=False
        )

        for result in results:

            boxes = result.boxes

            for box in boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id not in vehicle_classes:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                label = vehicle_classes[class_id]

                text = f"{label} {confidence:.2f}"

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    text,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        writer.write(frame)

        cv2.imshow(
            "SIH 26127 - Vehicle Detection",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print("✅ Output saved:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()