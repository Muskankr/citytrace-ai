import cv2
from ultralytics import YOLO


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_PATH = "data/videos/sih_traffic.mp4"

# GitHub repository's trained license plate model
MODEL_PATH = "models/license_plate_github.pt"

OUTPUT_PATH = "outputs/videos/github_plate_test.mp4"

CONFIDENCE = 0.20


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("GITHUB LICENSE PLATE MODEL TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Load license plate model
    # --------------------------------------------------------

    print("\nLoading license plate model...")

    model = YOLO(MODEL_PATH)

    print("✅ License plate model loaded")

    # --------------------------------------------------------
    # Open video
    # --------------------------------------------------------

    print("\nOpening video...")

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print("❌ Could not open video:")
        print(VIDEO_PATH)
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video resolution : {width} x {height}")
    print(f"FPS              : {fps}")
    print(f"Total frames     : {total_frames}")

    # --------------------------------------------------------
    # Create output video
    # --------------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    out = cv2.VideoWriter(
        OUTPUT_PATH,
        fourcc,
        fps,
        (width, height)
    )

    # --------------------------------------------------------
    # Process video
    # --------------------------------------------------------

    frame_number = 0
    total_detections = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Run license plate detector
        results = model(
            frame,
            conf=CONFIDENCE,
            verbose=False
        )

        detections = results[0].boxes.data.tolist()

        for detection in detections:

            x1, y1, x2, y2, confidence, class_id = detection

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)

            total_detections += 1

            # Draw plate bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Display confidence
            label = f"PLATE {confidence:.2f}"

            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # Write processed frame
        out.write(frame)

        frame_number += 1

        if frame_number % 100 == 0:

            print(
                f"Processed {frame_number}/{total_frames} "
                f"| detections: {total_detections}"
            )

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    cap.release()
    out.release()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    print(f"Total plate detections : {total_detections}")
    print(f"Output video           : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()