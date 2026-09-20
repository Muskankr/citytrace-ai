import os
import cv2
from ultralytics import YOLO
import easyocr

from src.ocr import process_plate
from src.validator import validate_plate
from src.database_logger import save_detection


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_PATH = "data/videos/sih_traffic.mp4"

VEHICLE_MODEL = "yolo26n.pt"
PLATE_MODEL = "models/license_plate.pt"

CAMERA_CODE = "CAM001"

VEHICLE_CONF = 0.40
PLATE_CONF = 0.20

PLATE_INTERVAL = 4

MIN_VEHICLE_WIDTH = 100
MIN_VEHICLE_HEIGHT = 60

OUTPUT_VIDEO = "outputs/videos/master_pipeline.mp4"
TEMP_PLATE_DIR = "outputs/pipeline_plates"


# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


# ============================================================
# CREATE FOLDERS
# ============================================================

os.makedirs("outputs/videos", exist_ok=True)
os.makedirs(TEMP_PLATE_DIR, exist_ok=True)


# ============================================================
# SHARPNESS
# ============================================================

def calculate_sharpness(image):

    if image is None or image.size == 0:
        return 0.0

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )


# ============================================================
# QUALITY SCORE
# ============================================================

def calculate_quality_score(
    crop,
    detector_conf
):

    if crop is None or crop.size == 0:
        return 0.0

    height, width = crop.shape[:2]

    if width < 20 or height < 8:
        return 0.0

    sharpness = calculate_sharpness(crop)

    sharpness_score = min(
        sharpness / 500.0,
        1.0
    )

    area = width * height

    resolution_score = min(
        area / 5000.0,
        1.0
    )

    confidence_score = float(
        detector_conf
    )

    return (
        0.60 * sharpness_score
        + 0.25 * resolution_score
        + 0.15 * confidence_score
    )


# ============================================================
# ENLARGE PLATE
# ============================================================

def enlarge_plate(crop):

    return cv2.resize(
        crop,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()
    print("=" * 70)
    print("        SIH26127 MASTER AI ANPR PIPELINE")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # LOAD MODELS
    # --------------------------------------------------------

    print("Loading vehicle detection model...")

    vehicle_model = YOLO(
        VEHICLE_MODEL
    )

    print("Loading license plate model...")

    plate_model = YOLO(
        PLATE_MODEL
    )

    print("Loading OCR engine...")

    reader = easyocr.Reader(
        ["en"],
        gpu=False
    )

    print("✅ All AI models loaded.")
    print()

    # --------------------------------------------------------
    # OPEN VIDEO
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            f"❌ Could not open video: "
            f"{VIDEO_PATH}"
        )

        return

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 30

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print("VIDEO INFORMATION")
    print("-" * 70)
    print(f"Camera       : {CAMERA_CODE}")
    print(f"Resolution   : {width} x {height}")
    print(f"FPS          : {fps:.2f}")
    print(f"Total frames : {total_frames}")
    print()

    # --------------------------------------------------------
    # OUTPUT VIDEO
    # --------------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    out = cv2.VideoWriter(
        OUTPUT_VIDEO,
        fourcc,
        fps,
        (width, height)
    )

    # --------------------------------------------------------
    # BEST PLATE DATA
    # --------------------------------------------------------

    track_data = {}

    frame_number = 0

    # ========================================================
    # VIDEO LOOP
    # ========================================================

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame_number += 1

        clean_frame = frame.copy()

        # ----------------------------------------------------
        # VEHICLE DETECTION + TRACKING
        # ----------------------------------------------------

        results = vehicle_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=VEHICLE_CONF,
            classes=list(
                VEHICLE_CLASSES.keys()
            ),
            verbose=False
        )

        if len(results) == 0:

            out.write(frame)
            continue

        result = results[0]

        if (
            result.boxes is None
            or result.boxes.id is None
        ):

            out.write(frame)
            continue

        boxes = (
            result.boxes.xyxy
            .cpu()
            .numpy()
        )

        track_ids = (
            result.boxes.id
            .cpu()
            .numpy()
            .astype(int)
        )

        classes = (
            result.boxes.cls
            .cpu()
            .numpy()
            .astype(int)
        )

        vehicle_confidences = (
            result.boxes.conf
            .cpu()
            .numpy()
        )

        # ----------------------------------------------------
        # DRAW + PROCESS VEHICLES
        # ----------------------------------------------------

        for (
            box,
            track_id,
            class_id,
            vehicle_conf
        ) in zip(
            boxes,
            track_ids,
            classes,
            vehicle_confidences
        ):

            if class_id not in VEHICLE_CLASSES:
                continue

            x1, y1, x2, y2 = map(
                int,
                box
            )

            x1 = max(0, x1)
            y1 = max(0, y1)

            x2 = min(width, x2)
            y2 = min(height, y2)

            vehicle_width = x2 - x1
            vehicle_height = y2 - y1

            if (
                vehicle_width <= 0
                or vehicle_height <= 0
            ):
                continue

            vehicle_name = VEHICLE_CLASSES[
                class_id
            ]

            # ------------------------------------------------
            # DRAW VEHICLE
            # ------------------------------------------------

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
                (
                    x1,
                    max(25, y1 - 8)
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 0, 0),
                2
            )

            # ------------------------------------------------
            # PLATE DETECTION EVERY N FRAMES
            # ------------------------------------------------

            if (
                frame_number
                % PLATE_INTERVAL
                != 0
            ):
                continue

            if (
                vehicle_width
                < MIN_VEHICLE_WIDTH
                or vehicle_height
                < MIN_VEHICLE_HEIGHT
            ):
                continue

            vehicle_crop = clean_frame[
                y1:y2,
                x1:x2
            ]

            if vehicle_crop.size == 0:
                continue

            # ------------------------------------------------
            # LICENSE PLATE MODEL
            # ------------------------------------------------

            plate_results = (
                plate_model.predict(
                    vehicle_crop,
                    conf=PLATE_CONF,
                    imgsz=640,
                    verbose=False
                )
            )

            if len(plate_results) == 0:
                continue

            plate_result = plate_results[0]

            if plate_result.boxes is None:
                continue

            # ------------------------------------------------
            # PLATE CANDIDATES
            # ------------------------------------------------

            for (
                plate_box,
                plate_conf
            ) in zip(
                plate_result.boxes.xyxy
                .cpu()
                .numpy(),

                plate_result.boxes.conf
                .cpu()
                .numpy()
            ):

                px1, py1, px2, py2 = map(
                    int,
                    plate_box
                )

                vh, vw = (
                    vehicle_crop.shape[:2]
                )

                px1 = max(0, px1)
                py1 = max(0, py1)

                px2 = min(vw, px2)
                py2 = min(vh, py2)

                plate_width = (
                    px2 - px1
                )

                plate_height = (
                    py2 - py1
                )

                if (
                    plate_width < 25
                    or plate_height < 8
                ):
                    continue

                plate_crop = vehicle_crop[
                    py1:py2,
                    px1:px2
                ].copy()

                if plate_crop.size == 0:
                    continue

                # ------------------------------------------------
                # QUALITY
                # ------------------------------------------------

                sharpness = (
                    calculate_sharpness(
                        plate_crop
                    )
                )

                quality = (
                    calculate_quality_score(
                        plate_crop,
                        float(plate_conf)
                    )
                )

                # ------------------------------------------------
                # STORE BEST PLATE
                # ------------------------------------------------

                if (
                    track_id not in track_data
                    or quality
                    > track_data[track_id]["quality"]
                ):

                    track_data[track_id] = {

                        "crop": plate_crop,

                        "quality": quality,

                        "sharpness": sharpness,

                        "plate_confidence":
                            float(plate_conf),

                        "vehicle_confidence":
                            float(vehicle_conf),

                        "vehicle_type":
                            vehicle_name,

                        "frame":
                            frame_number,
                    }

                # ------------------------------------------------
                # DRAW PLATE
                # ------------------------------------------------

                gx1 = x1 + px1
                gy1 = y1 + py1
                gx2 = x1 + px2
                gy2 = y1 + py2

                cv2.rectangle(
                    frame,
                    (gx1, gy1),
                    (gx2, gy2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"PLATE {plate_conf:.2f}",
                    (
                        gx1,
                        max(
                            20,
                            gy1 - 5
                        )
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (0, 255, 0),
                    1
                )

        # ----------------------------------------------------
        # WRITE FRAME
        # ----------------------------------------------------

        out.write(frame)

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        if frame_number % 50 == 0:

            progress = (
                frame_number
                / total_frames
                * 100
            )

            print(
                f"Processing: "
                f"{frame_number}/{total_frames} "
                f"({progress:.1f}%)"
            )

    # ========================================================
    # RELEASE VIDEO
    # ========================================================

    cap.release()
    out.release()

    print()
    print("=" * 70)
    print("VIDEO PROCESSING COMPLETE")
    print("=" * 70)
    print(
        f"Tracks with plate candidates: "
        f"{len(track_data)}"
    )
    print(
        f"Output video: {OUTPUT_VIDEO}"
    )
    print()

    # ========================================================
    # OCR + VALIDATION + DATABASE
    # ========================================================

    print("=" * 70)
    print("OCR + VALIDATION + DATABASE")
    print("=" * 70)
    print()

    successful_detections = 0

    for track_id, data in track_data.items():

        crop = data["crop"]

        if (
            crop is None
            or crop.size == 0
        ):
            continue

        # ----------------------------------------------------
        # SAVE TEMPORARY PLATE
        # ----------------------------------------------------

        temp_filename = (
            f"track_{track_id}.jpg"
        )

        temp_path = os.path.join(
            TEMP_PLATE_DIR,
            temp_filename
        )

        enlarged = enlarge_plate(
            crop
        )

        cv2.imwrite(
            temp_path,
            enlarged,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                95
            ]
        )

        # ----------------------------------------------------
        # OCR
        #
        # process_plate() expects the
        # image inside outputs/plates.
        # So copy it there temporarily.
        # ----------------------------------------------------

        final_ocr_path = os.path.join(
            "outputs/plates",
            temp_filename
        )

        cv2.imwrite(
            final_ocr_path,
            enlarged,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                95
            ]
        )

        try:

            ocr_result = process_plate(
                reader,
                temp_filename
            )

        except Exception as error:

            print(
                f"❌ OCR failed for "
                f"Track {track_id}: "
                f"{error}"
            )

            continue

        if ocr_result is None:
            continue

        ocr_text = ocr_result["text"]

        ocr_confidence = (
            ocr_result["confidence"]
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        validation = validate_plate(
            ocr_text,
            ocr_confidence
        )

        plate_number = (
            validation["plate_number"]
        )

        plate_valid = (
            validation["valid"]
        )

        plate_status = (
            validation["status"]
        )

        # ----------------------------------------------------
        # DISPLAY RESULT
        # ----------------------------------------------------

        print(
            f"Track {track_id}"
        )

        print(
            f"  OCR       : {ocr_text}"
        )

        print(
            f"  OCR Conf  : "
            f"{ocr_confidence:.2f}"
        )

        print(
            f"  Validation: "
            f"{plate_status}"
        )

        print(
            f"  Quality   : "
            f"{data['quality']:.3f}"
        )

        # ----------------------------------------------------
        # SAVE VALID DETECTION
        # ----------------------------------------------------

        if plate_valid:

            saved = save_detection(

                camera_code=CAMERA_CODE,

                track_id=track_id,

                vehicle_type=data[
                    "vehicle_type"
                ],

                plate_number=plate_number,

                ocr_confidence=ocr_confidence,

                plate_valid=True,

                plate_status=plate_status,

                frame_number=data[
                    "frame"
                ],

                vehicle_confidence=data[
                    "vehicle_confidence"
                ],

                plate_detection_confidence=data[
                    "plate_confidence"
                ],
            )

            if saved:
                successful_detections += 1

        else:

            print(
                "  ⚠ Detection not saved "
                "as a valid plate."
            )

        print()

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("=" * 70)
    print("          MASTER PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"Plate candidates : "
        f"{len(track_data)}"
    )

    print(
        f"Valid DB records : "
        f"{successful_detections}"
    )

    print(
        f"Video output     : "
        f"{OUTPUT_VIDEO}"
    )

    print()
    print(
        "Next stage:"
    )
    print(
        "Trajectory → Analytics → Alerts → Dashboard"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()