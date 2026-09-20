from ultralytics import YOLO
import cv2


MODEL_PATH = "yolo26n.pt"
VIDEO_PATH = "data/videos/traffic.mp4"


def main():

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print("❌ Could not open video")
        return

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

        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.40,
            verbose=False
        )

        for result in results:

            if result.boxes.id is None:
                continue

            boxes = result.boxes

            track_ids = boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):

                class_id = int(box.cls[0])

                if class_id not in vehicle_classes:
                    continue

                confidence = float(box.conf[0])

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                label = (
                    f"{vehicle_classes[class_id]} "
                    f"ID:{track_id} "
                    f"{confidence:.2f}"
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 0, 0),
                    2
                )

        cv2.imshow(
            "SIH 26127 - Vehicle Tracking",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()