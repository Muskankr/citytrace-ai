import cv2
import os
import numpy as np
from ultralytics import YOLO

# ==============================
# CONFIGURATION
# ==============================

VIDEO_PATH = "data/videos/traffic.mp4"

VEHICLE_MODEL = "yolo26n.pt"
PLATE_MODEL = "models/license_plate.pt"

OUTPUT_VIDEO = "outputs/videos/plate_detection_quality.mp4"
PLATE_OUTPUT_DIR = "outputs/plates"

VEHICLE_CONF = 0.40
PLATE_CONF = 0.20

# Run plate detection every N frames
PLATE_INTERVAL = 4

# Ignore very small vehicles
MIN_VEHICLE_WIDTH = 100
MIN_VEHICLE_HEIGHT = 60

# Keep best crop for each vehicle
MAX_CANDIDATES_PER_TRACK = 10


# COCO vehicle classes
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


# ==============================
# FOLDERS
# ==============================

os.makedirs(PLATE_OUTPUT_DIR, exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)


# ==============================
# SHARPNESS FUNCTION
# ==============================

def calculate_sharpness(image):
    """
    Measures image sharpness using Laplacian variance.

    Higher value = sharper image.
    """

    if image is None or image.size == 0:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# ==============================
# PLATE QUALITY SCORE
# ==============================

def calculate_quality_score(crop, detector_conf):
    """
    Combines:
    - image sharpness
    - plate size
    - detector confidence

    Sharpness is given the highest importance.
    """

    if crop is None or crop.size == 0:
        return 0.0

    height, width = crop.shape[:2]

    sharpness = calculate_sharpness(crop)

    # Avoid extremely small crops
    if width < 20 or height < 8:
        return 0.0

    # Resolution score
    area = width * height
    resolution_score = min(area / 5000.0, 1.0)

    # Normalize sharpness
    sharpness_score = min(sharpness / 500.0, 1.0)

    # Detector confidence
    confidence_score = float(detector_conf)

    # Final weighted score
    score = (
        0.60 * sharpness_score
        + 0.25 * resolution_score
        + 0.15 * confidence_score
    )

    return score


# ==============================
# ENLARGE PLATE
# ==============================

def enlarge_plate(crop):
    """
    Enlarges the crop for easier OCR.
    This does NOT create new information;
    it only makes the existing pixels larger.
    """

    if crop is None or crop.size == 0:
        return crop

    return cv2.resize(
        crop,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )


# ==============================
# MAIN
# ==============================

print("Loading vehicle model...")
vehicle_model = YOLO(VEHICLE_MODEL)

print("Loading plate model...")
plate_model = YOLO(PLATE_MODEL)


# ==============================
# VIDEO SETUP
# ==============================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError(
        f"Could not open video: {VIDEO_PATH}"
    )

fps = cap.get(cv2.CAP_PROP_FPS)

if fps <= 0:
    fps = 30

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print()
print("======================================")
print("VIDEO INFORMATION")
print("======================================")
print(f"Resolution: {width} x {height}")
print(f"FPS: {fps:.2f}")
print(f"Total frames: {total_frames}")
print("======================================")


# ==============================
# OUTPUT VIDEO
# ==============================

fourcc = cv2.VideoWriter_fourcc(*"mp4v")

out = cv2.VideoWriter(
    OUTPUT_VIDEO,
    fourcc,
    fps,
    (width, height)
)


# ==============================
# TRACK DATA
# ==============================

# Structure:
#
# track_data = {
#     track_id: {
#         "crop": best_crop,
#         "score": best_score,
#         "confidence": detector_conf,
#         "frame": frame_number,
#         "sharpness": sharpness
#     }
# }

track_data = {}

frame_number = 0


# ==============================
# PROCESS VIDEO
# ==============================

while True:

    success, frame = cap.read()

    if not success:
        break

    frame_number += 1

    # Keep completely clean frame.
    # Important: plate crops must NOT come from
    # a frame containing tracking labels.
    clean_frame = frame.copy()

    # ==========================================
    # VEHICLE DETECTION + TRACKING
    # ==========================================

    results = vehicle_model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=VEHICLE_CONF,
        classes=list(VEHICLE_CLASSES.keys()),
        verbose=False
    )

    if len(results) == 0:
        out.write(frame)
        continue

    result = results[0]

    # ==========================================
    # CHECK TRACK IDs
    # ==========================================

    if result.boxes is None or result.boxes.id is None:

        out.write(frame)
        continue

    boxes = result.boxes.xyxy.cpu().numpy()
    track_ids = result.boxes.id.cpu().numpy().astype(int)
    classes = result.boxes.cls.cpu().numpy().astype(int)
    confidences = result.boxes.conf.cpu().numpy()

    # ==========================================
    # DRAW VEHICLES
    # ==========================================

    for box, track_id, cls_id, vehicle_conf in zip(
        boxes,
        track_ids,
        classes,
        confidences
    ):

        x1, y1, x2, y2 = map(int, box)

        vehicle_name = VEHICLE_CLASSES.get(
            cls_id,
            "vehicle"
        )

        # Keep coordinates inside frame
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)

        vehicle_width = x2 - x1
        vehicle_height = y2 - y1

        if vehicle_width <= 0 or vehicle_height <= 0:
            continue

        # Draw vehicle box
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            2
        )

        cv2.putText(
            frame,
            f"{vehicle_name} ID:{track_id}",
            (x1, max(25, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 0, 0),
            2
        )


    # ==========================================
    # PLATE DETECTION
    # ==========================================

    if frame_number % PLATE_INTERVAL == 0:

        for box, track_id in zip(boxes, track_ids):

            x1, y1, x2, y2 = map(int, box)

            # Clamp coordinates
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)

            vehicle_width = x2 - x1
            vehicle_height = y2 - y1

            # Ignore distant/tiny vehicles
            if (
                vehicle_width < MIN_VEHICLE_WIDTH
                or vehicle_height < MIN_VEHICLE_HEIGHT
            ):
                continue

            # ==================================
            # CLEAN VEHICLE CROP
            # ==================================

            vehicle_crop = clean_frame[
                y1:y2,
                x1:x2
            ]

            if vehicle_crop.size == 0:
                continue

            # ==================================
            # PLATE MODEL
            # ==================================

            plate_results = plate_model.predict(
                vehicle_crop,
                conf=PLATE_CONF,
                imgsz=640,
                verbose=False
            )

            if len(plate_results) == 0:
                continue

            plate_result = plate_results[0]

            if plate_result.boxes is None:
                continue

            # ==================================
            # FIND PLATE CANDIDATES
            # ==================================

            for plate_box, plate_conf in zip(
                plate_result.boxes.xyxy.cpu().numpy(),
                plate_result.boxes.conf.cpu().numpy()
            ):

                px1, py1, px2, py2 = map(
                    int,
                    plate_box
                )

                # Clamp plate coordinates
                vh, vw = vehicle_crop.shape[:2]

                px1 = max(0, px1)
                py1 = max(0, py1)
                px2 = min(vw, px2)
                py2 = min(vh, py2)

                plate_width = px2 - px1
                plate_height = py2 - py1

                if plate_width <= 0 or plate_height <= 0:
                    continue

                # Reject extremely tiny plates
                if plate_width < 25 or plate_height < 8:
                    continue

                # ==================================
                # EXTRACT PLATE
                # ==================================

                plate_crop = vehicle_crop[
                    py1:py2,
                    px1:px2
                ].copy()

                if plate_crop.size == 0:
                    continue

                # ==================================
                # QUALITY CALCULATION
                # ==================================

                sharpness = calculate_sharpness(
                    plate_crop
                )

                quality_score = calculate_quality_score(
                    plate_crop,
                    float(plate_conf)
                )

                # ==================================
                # STORE BEST OBSERVATION
                # ==================================

                if track_id not in track_data:

                    track_data[track_id] = {
                        "crop": plate_crop,
                        "score": quality_score,
                        "confidence": float(plate_conf),
                        "frame": frame_number,
                        "sharpness": sharpness
                    }

                    print(
                        f"New plate candidate | "
                        f"Track {track_id} | "
                        f"Quality {quality_score:.3f} | "
                        f"Sharpness {sharpness:.1f}"
                    )

                else:

                    current_best = track_data[
                        track_id
                    ]["score"]

                    if quality_score > current_best:

                        track_data[track_id] = {
                            "crop": plate_crop,
                            "score": quality_score,
                            "confidence": float(plate_conf),
                            "frame": frame_number,
                            "sharpness": sharpness
                        }

                        print(
                            f"⬆ Better plate | "
                            f"Track {track_id} | "
                            f"Quality {quality_score:.3f} | "
                            f"Sharpness {sharpness:.1f}"
                        )

                # ==================================
                # DRAW PLATE ON VIDEO
                # ==================================

                global_x1 = x1 + px1
                global_y1 = y1 + py1
                global_x2 = x1 + px2
                global_y2 = y1 + py2

                cv2.rectangle(
                    frame,
                    (global_x1, global_y1),
                    (global_x2, global_y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"PLATE {plate_conf:.2f}",
                    (
                        global_x1,
                        max(20, global_y1 - 5)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (0, 255, 0),
                    1
                )


    # ==========================================
    # WRITE OUTPUT FRAME
    # ==========================================

    out.write(frame)


# ==============================
# RELEASE VIDEO
# ==============================

cap.release()
out.release()


# ==============================
# SAVE BEST PLATES
# ==============================

print()
print("Saving best-quality plate crops...")
print()

saved_count = 0

for track_id, data in track_data.items():

    crop = data["crop"]

    if crop is None or crop.size == 0:
        continue

    # Enlarge only after selecting the best
    # original crop.
    enlarged = enlarge_plate(crop)

    output_path = os.path.join(
        PLATE_OUTPUT_DIR,
        f"track_{track_id}_best.jpg"
    )

    cv2.imwrite(
        output_path,
        enlarged,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            95
        ]
    )

    saved_count += 1

    print(
        f"Track {track_id}: "
        f"quality={data['score']:.3f}, "
        f"sharpness={data['sharpness']:.1f}, "
        f"confidence={data['confidence']:.2f}, "
        f"frame={data['frame']}"
    )


# ==============================
# FINAL REPORT
# ==============================

print()
print("======================================")
print("✅ QUALITY-BASED PLATE DETECTION DONE")
print("======================================")
print(f"Tracked vehicles with plates: {len(track_data)}")
print(f"Best plate crops saved: {saved_count}")
print()
print(f"Video:")
print(OUTPUT_VIDEO)
print()
print(f"Plate crops:")
print(PLATE_OUTPUT_DIR)
print("======================================")