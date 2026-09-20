import os
import csv
import cv2

from collections import defaultdict

from ultralytics import YOLO
from rapidocr import RapidOCR

from src.pipeline import run_ocr, choose_consensus
from src.ocr_correction import normalize_plate


# ============================================================
# CONFIG
# ============================================================

VIDEO_PATH = "data/videos/sih_traffic.mp4"

VEHICLE_MODEL = "yolo26n.pt"
PLATE_MODEL = "models/license_plate_github.pt"

GROUND_TRUTH = "data/benchmark/ground_truth.csv"

OUTPUT_CSV = "data/benchmark/full_temporal_results.csv"

VEHICLE_CONF = 0.40
PLATE_CONF = 0.20

PROCESS_EVERY_N_FRAMES = 4

MIN_VEHICLE_WIDTH = 80
MIN_VEHICLE_HEIGHT = 50

# Only benchmark vehicles for which we have ground truth.
TARGET_TRACKS = {
    1,
    5,
    7,
    25,
    28,
    35,
    54,
    64,
    67,
    73,
    86,
    95,
}


# ============================================================
# GROUND TRUTH
# ============================================================

def load_ground_truth():

    records = {}

    with open(
        GROUND_TRUTH,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            track_id = int(row["track_id"])

            actual = normalize_plate(
                row["actual_plate"]
            )

            records[track_id] = actual

    return records


# ============================================================
# DISTANCE
# ============================================================

def levenshtein_distance(a, b):

    if a == b:
        return 0

    if not a:
        return len(b)

    if not b:
        return len(a)

    previous = list(range(len(b) + 1))

    for i, char_a in enumerate(a, start=1):

        current = [i]

        for j, char_b in enumerate(b, start=1):

            insertion = current[j - 1] + 1
            deletion = previous[j] + 1

            substitution = (
                previous[j - 1]
                + (char_a != char_b)
            )

            current.append(
                min(
                    insertion,
                    deletion,
                    substitution
                )
            )

        previous = current

    return previous[-1]


def character_accuracy(actual, predicted):

    if not actual or not predicted:
        return 0.0

    distance = levenshtein_distance(
        actual,
        predicted
    )

    return max(
        0.0,
        1.0 - (
            distance
            / max(len(actual), len(predicted))
        )
    )


# ============================================================
# PLATE DETECTION
# ============================================================

def detect_plate(
    plate_model,
    vehicle_crop
):

    if (
        vehicle_crop is None
        or vehicle_crop.size == 0
    ):
        return None

    result = plate_model.predict(
        vehicle_crop,
        conf=PLATE_CONF,
        verbose=False
    )[0]

    if result.boxes is None:
        return None

    best = None
    best_confidence = 0.0

    for box in result.boxes:

        confidence = float(
            box.conf[0]
        )

        if confidence < best_confidence:
            continue

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0].tolist()
        )

        height, width = (
            vehicle_crop.shape[:2]
        )

        x1 = max(0, min(x1, width - 1))
        x2 = max(0, min(x2, width))

        y1 = max(0, min(y1, height - 1))
        y2 = max(0, min(y2, height))

        if x2 <= x1 or y2 <= y1:
            continue

        crop = vehicle_crop[
            y1:y2,
            x1:x2
        ]

        if crop.size == 0:
            continue

        best = crop
        best_confidence = confidence

    if best is None:
        return None

    return best, best_confidence


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 75)
    print("SIH26127 FULL TEMPORAL ANPR BENCHMARK")
    print("=" * 75)
    print()

    ground_truth = load_ground_truth()

    print(
        f"Ground-truth vehicles : "
        f"{len(ground_truth)}"
    )

    print(
        f"Target tracks         : "
        f"{sorted(TARGET_TRACKS)}"
    )

    print()

    vehicle_model = YOLO(
        VEHICLE_MODEL
    )

    plate_model = YOLO(
        PLATE_MODEL
    )

    reader = RapidOCR()

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            f"ERROR: Could not open "
            f"{VIDEO_PATH}"
        )

        return

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    print(
        f"Video frames : {frame_count}"
    )

    print(
        f"FPS          : {fps:.2f}"
    )

    print()

    # --------------------------------------------------------
    # observations[track_id] = list of OCR observations
    # --------------------------------------------------------

    observations = defaultdict(list)

    frame_number = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame_number += 1

        if (
            frame_number
            % PROCESS_EVERY_N_FRAMES
            != 0
        ):
            continue

        # ----------------------------------------------------
        # Vehicle tracking
        # ----------------------------------------------------

        results = vehicle_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=VEHICLE_CONF,
            verbose=False
        )

        if not results:
            continue

        result = results[0]

        if result.boxes is None:
            continue

        boxes = result.boxes

        if boxes.id is None:
            continue

        track_ids = (
            boxes.id
            .int()
            .cpu()
            .tolist()
        )

        classes = (
            boxes.cls
            .int()
            .cpu()
            .tolist()
        )

        xyxy = (
            boxes.xyxy
            .int()
            .cpu()
            .tolist()
        )

        for track_id, class_id, box in zip(
            track_ids,
            classes,
            xyxy
        ):

            if track_id not in TARGET_TRACKS:
                continue

            if track_id not in ground_truth:
                continue

            # COCO vehicle classes
            if class_id not in {
                2, 3, 5, 7
            }:
                continue

            x1, y1, x2, y2 = box

            x1 = max(
                0,
                x1
            )

            y1 = max(
                0,
                y1
            )

            x2 = min(
                frame.shape[1],
                x2
            )

            y2 = min(
                frame.shape[0],
                y2
            )

            width = x2 - x1
            height = y2 - y1

            if (
                width < MIN_VEHICLE_WIDTH
                or height < MIN_VEHICLE_HEIGHT
            ):
                continue

            vehicle_crop = frame[
                y1:y2,
                x1:x2
            ]

            detected = detect_plate(
                plate_model,
                vehicle_crop
            )

            if detected is None:
                continue

            plate_crop, plate_confidence = (
                detected
            )

            # ------------------------------------------------
            # OCR
            # ------------------------------------------------

            ocr_result = run_ocr(
                reader,
                plate_crop
            )

            if not ocr_result:
                continue

            candidates = ocr_result.get(
                "candidates",
                []
            )

            if not candidates:

                candidates = [
                    {
                        "text": ocr_result.get(
                            "text",
                            ""
                        ),
                        "confidence":
                            ocr_result.get(
                                "confidence",
                                0.0
                            ),
                        "method":
                            ocr_result.get(
                                "method",
                                "unknown"
                            )
                    }
                ]

            crop_height, crop_width = (
                plate_crop.shape[:2]
            )

            resolution = (
                crop_width
                * crop_height
            )

            for candidate in candidates:

                text = normalize_plate(
                    candidate.get(
                        "text",
                        ""
                    )
                )

                if not text:
                    continue

                confidence = float(
                    candidate.get(
                        "confidence",
                        0.0
                    )
                )

                observations[
                    track_id
                ].append(
                    {
                        "text": text,
                        "confidence": confidence,
                        "quality": 0.8,
                        "sharpness": 1.0,
                        "frame": frame_number,
                        "plate_confidence":
                            plate_confidence,
                        "resolution":
                            resolution,
                        "interpolated": False
                    }
                )

        if frame_number % 300 == 0:

            print(
                f"Processed "
                f"{frame_number}/{frame_count} "
                f"frames..."
            )

    cap.release()

    print()
    print("=" * 75)
    print("OCR COLLECTION COMPLETE")
    print("=" * 75)
    print()

    # ========================================================
    # FINAL CONSENSUS
    # ========================================================

    os.makedirs(
        os.path.dirname(
            OUTPUT_CSV
        ),
        exist_ok=True
    )

    rows = []

    total = 0
    exact_matches = 0

    character_scores = []
    edit_distances = []

    for track_id in sorted(
        ground_truth
    ):

        actual = ground_truth[
            track_id
        ]

        track_observations = observations.get(
            track_id,
            []
        )

        print(
            f"Track {track_id}: "
            f"{len(track_observations)} "
            f"OCR observations"
        )

        if not track_observations:

            predicted = ""

            consensus_confidence = 0.0
            consensus_count = 0

        else:

            consensus = choose_consensus(
                track_observations
            )

            if consensus:

                predicted = normalize_plate(
                    consensus.get(
                        "text",
                        ""
                    )
                )

                consensus_confidence = float(
                    consensus.get(
                        "confidence",
                        0.0
                    )
                )

                consensus_count = int(
                    consensus.get(
                        "count",
                        0
                    )
                )

            else:

                predicted = ""

                consensus_confidence = 0.0
                consensus_count = 0

        distance = levenshtein_distance(
            actual,
            predicted
        )

        char_accuracy = (
            character_accuracy(
                actual,
                predicted
            )
        )

        exact = (
            bool(predicted)
            and predicted == actual
        )

        total += 1

        if exact:
            exact_matches += 1

        character_scores.append(
            char_accuracy
        )

        edit_distances.append(
            distance
        )

        status = (
            "CORRECT"
            if exact
            else "WRONG"
        )

        print(
            f"  Actual     : {actual}"
        )

        print(
            f"  Predicted  : "
            f"{predicted or 'UNREADABLE'}"
        )

        print(
            f"  Confidence : "
            f"{consensus_confidence:.3f}"
        )

        print(
            f"  Evidence   : "
            f"{consensus_count}"
        )

        print(
            f"  Result     : {status}"
        )

        print(
            f"  Character  : "
            f"{char_accuracy:.1%}"
        )

        print()

        rows.append(
            {
                "track_id": track_id,
                "actual_plate": actual,
                "predicted_plate": predicted,
                "exact_match": exact,
                "character_accuracy":
                    round(
                        char_accuracy,
                        4
                    ),
                "edit_distance": distance,
                "ocr_confidence":
                    round(
                        consensus_confidence,
                        4
                    ),
                "observation_count":
                    len(track_observations),
                "consensus_count":
                    consensus_count
            }
        )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "track_id",
                "actual_plate",
                "predicted_plate",
                "exact_match",
                "character_accuracy",
                "edit_distance",
                "ocr_confidence",
                "observation_count",
                "consensus_count"
            ]
        )

        writer.writeheader()

        writer.writerows(rows)

    # ========================================================
    # SUMMARY
    # ========================================================

    if total == 0:

        print(
            "No benchmark samples found."
        )

        return

    exact_accuracy = (
        exact_matches / total
    )

    average_character_accuracy = (
        sum(character_scores)
        / len(character_scores)
    )

    average_edit_distance = (
        sum(edit_distances)
        / len(edit_distances)
    )

    print("=" * 75)
    print("FINAL TEMPORAL BENCHMARK")
    print("=" * 75)

    print(
        f"Samples tested          : "
        f"{total}"
    )

    print(
        f"Exact recognitions      : "
        f"{exact_matches}/{total}"
    )

    print(
        f"Exact plate accuracy    : "
        f"{exact_accuracy:.1%}"
    )

    print(
        f"Character accuracy      : "
        f"{average_character_accuracy:.1%}"
    )

    print(
        f"Average edit distance   : "
        f"{average_edit_distance:.2f}"
    )

    print()

    print(
        f"Results saved to        : "
        f"{OUTPUT_CSV}"
    )

    print("=" * 75)

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This benchmark measures the "
        "current implementation on the "
        "available labeled video tracks."
    )

    print(
        "A >90% result should only be "
        "claimed after sufficient labeled "
        "samples and representative "
        "conditions have been evaluated."
    )


if __name__ == "__main__":
    main()