import os
import csv
import cv2

from collections import defaultdict, Counter

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

# NEW:
# Stores every OCR observation so we can inspect what RapidOCR
# actually saw before consensus.
OBSERVATION_CSV = (
    "data/benchmark/ocr_observations.csv"
)

VEHICLE_CONF = 0.40
PLATE_CONF = 0.20

# ByteTrack runs on EVERY frame.
# Plate detection + OCR runs every Nth frame.
PROCESS_EVERY_N_FRAMES = 4

MIN_VEHICLE_WIDTH = 80
MIN_VEHICLE_HEIGHT = 50

VEHICLE_CLASSES = {
    2,  # car
    3,  # motorcycle
    5,  # bus
    7,  # truck
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

            track_id = int(
                row["track_id"]
            )

            actual = normalize_plate(
                row["actual_plate"]
            )

            records[track_id] = actual

    return records


# ============================================================
# LEVENSHTEIN DISTANCE
# ============================================================

def levenshtein_distance(a, b):

    if a == b:
        return 0

    if not a:
        return len(b)

    if not b:
        return len(a)

    previous = list(
        range(len(b) + 1)
    )

    for i, char_a in enumerate(
        a,
        start=1
    ):

        current = [i]

        for j, char_b in enumerate(
            b,
            start=1
        ):

            insertion = (
                current[j - 1] + 1
            )

            deletion = (
                previous[j] + 1
            )

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


# ============================================================
# CHARACTER ACCURACY
# ============================================================

def character_accuracy(
    actual,
    predicted
):

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
            / max(
                len(actual),
                len(predicted)
            )
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

    if (
        result.boxes is None
        or len(result.boxes) == 0
    ):
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

        x1 = max(
            0,
            min(x1, width - 1)
        )

        x2 = max(
            0,
            min(x2, width)
        )

        y1 = max(
            0,
            min(y1, height - 1)
        )

        y2 = max(
            0,
            min(y2, height)
        )

        if (
            x2 <= x1
            or y2 <= y1
        ):
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

    return (
        best,
        best_confidence
    )


# ============================================================
# SAVE OCR OBSERVATIONS
# ============================================================

def save_ocr_observations(
    observations,
    ground_truth
):

    os.makedirs(
        os.path.dirname(
            OBSERVATION_CSV
        ),
        exist_ok=True
    )

    rows = []

    for track_id in sorted(
        ground_truth
    ):

        actual = ground_truth[
            track_id
        ]

        for index, item in enumerate(
            observations.get(
                track_id,
                []
            ),
            start=1
        ):

            rows.append(
                {
                    "track_id":
                        track_id,

                    "actual_plate":
                        actual,

                    "observation_index":
                        index,

                    "frame":
                        item.get(
                            "frame",
                            ""
                        ),

                    "text":
                        item.get(
                            "text",
                            ""
                        ),

                    "confidence":
                        round(
                            float(
                                item.get(
                                    "confidence",
                                    0.0
                                )
                            ),
                            4
                        ),

                    "quality":
                        round(
                            float(
                                item.get(
                                    "quality",
                                    0.0
                                )
                            ),
                            4
                        ),

                    "sharpness":
                        round(
                            float(
                                item.get(
                                    "sharpness",
                                    0.0
                                )
                            ),
                            4
                        ),

                    "plate_confidence":
                        round(
                            float(
                                item.get(
                                    "plate_confidence",
                                    0.0
                                )
                            ),
                            4
                        ),

                    "resolution":
                        item.get(
                            "resolution",
                            0
                        ),

                    "method":
                        item.get(
                            "method",
                            ""
                        ),

                    "candidate_source":
                        item.get(
                            "candidate_source",
                            "raw"
                        ),

                    "interpolated":
                        item.get(
                            "interpolated",
                            False
                        )
                }
            )

    fieldnames = [
        "track_id",
        "actual_plate",
        "observation_index",
        "frame",
        "text",
        "confidence",
        "quality",
        "sharpness",
        "plate_confidence",
        "resolution",
        "method",
        "candidate_source",
        "interpolated"
    ]

    with open(
        OBSERVATION_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ============================================================
# PRINT OCR DIAGNOSTICS
# ============================================================

def print_ocr_diagnostics(
    observations,
    ground_truth
):

    print()
    print("=" * 75)
    print("OCR EVIDENCE DIAGNOSTICS")
    print("=" * 75)

    for track_id in sorted(
        ground_truth
    ):

        actual = ground_truth[
            track_id
        ]

        items = observations.get(
            track_id,
            []
        )

        if not items:
            print()
            print(
                f"Track {track_id}: "
                f"NO OCR OBSERVATIONS"
            )
            continue

        counter = Counter()

        for item in items:

            text = normalize_plate(
                item.get(
                    "text",
                    ""
                )
            )

            if text:
                counter[text] += 1

        print()
        print(
            f"Track {track_id} "
            f"(actual: {actual})"
        )

        print(
            f"  Total observations : "
            f"{len(items)}"
        )

        print(
            "  Most common OCR outputs:"
        )

        for text, count in counter.most_common(10):

            print(
                f"    {text:<15} "
                f"{count:>4} observations"
            )

        # ----------------------------------------------------
        # Check whether the actual plate appeared at all.
        # ----------------------------------------------------

        actual_count = counter.get(
            actual,
            0
        )

        print(
            f"  Exact actual plate "
            f"appeared : "
            f"{actual_count} times"
        )

        # ----------------------------------------------------
        # Show observations that differ from actual by only
        # one character.
        # ----------------------------------------------------

        near_matches = []

        for text, count in counter.items():

            distance = levenshtein_distance(
                actual,
                text
            )

            if distance == 1:

                near_matches.append(
                    (text, count)
                )

        near_matches.sort(
            key=lambda x: x[1],
            reverse=True
        )

        if near_matches:

            print(
                "  One-character variants:"
            )

            for text, count in near_matches[:10]:

                print(
                    f"    {text:<15} "
                    f"{count:>4} observations"
                )

    print()
    print("=" * 75)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 75)
    print("SIH26127 FULL TEMPORAL ANPR BENCHMARK")
    print("=" * 75)
    print()

    # --------------------------------------------------------
    # Load ground truth
    # --------------------------------------------------------

    ground_truth = load_ground_truth()

    print(
        f"Ground-truth vehicles : "
        f"{len(ground_truth)}"
    )

    print(
        f"Target tracks         : "
        f"{sorted(ground_truth.keys())}"
    )

    print()

    # --------------------------------------------------------
    # Load models
    # --------------------------------------------------------

    print(
        "Loading vehicle detector..."
    )

    vehicle_model = YOLO(
        VEHICLE_MODEL
    )

    print(
        "Loading license plate detector..."
    )

    plate_model = YOLO(
        PLATE_MODEL
    )

    print(
        "Loading RapidOCR..."
    )

    reader = RapidOCR()

    print()

    # --------------------------------------------------------
    # Open video
    # --------------------------------------------------------

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
    # observations[track_id] =
    # list of OCR observations
    # --------------------------------------------------------

    observations = defaultdict(list)

    track_seen_frames = defaultdict(int)

    track_plate_detections = defaultdict(int)

    frame_number = 0

    # ========================================================
    # VIDEO LOOP
    # ========================================================

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame_number += 1

        # ----------------------------------------------------
        # ByteTrack EVERY frame
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

        # ----------------------------------------------------
        # Count target vehicles whenever seen
        # ----------------------------------------------------

        for track_id in track_ids:

            if track_id in ground_truth:

                track_seen_frames[
                    track_id
                ] += 1

        # ----------------------------------------------------
        # Plate + OCR every N frames
        # ----------------------------------------------------

        if (
            frame_number
            % PROCESS_EVERY_N_FRAMES
            != 0
        ):
            continue

        # ====================================================
        # PLATE + OCR
        # ====================================================

        for (
            track_id,
            class_id,
            box
        ) in zip(
            track_ids,
            classes,
            xyxy
        ):

            if track_id not in ground_truth:
                continue

            if class_id not in VEHICLE_CLASSES:
                continue

            x1, y1, x2, y2 = box

            # ------------------------------------------------
            # Clamp coordinates
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Detect plate
            # ------------------------------------------------

            detected = detect_plate(
                plate_model,
                vehicle_crop
            )

            if detected is None:
                continue

            plate_crop, plate_confidence = (
                detected
            )

            track_plate_detections[
                track_id
            ] += 1

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

            # ------------------------------------------------
            # Fallback
            # ------------------------------------------------

            if not candidates:

                candidates = [
                    {
                        "text":
                            ocr_result.get(
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
                            ),

                        "candidate_source":
                            "raw",

                        "interpolated":
                            False
                    }
                ]

            crop_height, crop_width = (
                plate_crop.shape[:2]
            )

            resolution = (
                crop_width
                * crop_height
            )

            # ------------------------------------------------
            # Preserve ALL useful candidate metadata.
            # ------------------------------------------------

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

                # Preserve pipeline quality if supplied.
                # Otherwise retain the previous benchmark value.
                quality = float(
                    candidate.get(
                        "quality",
                        0.8
                    )
                )

                sharpness = float(
                    candidate.get(
                        "sharpness",
                        1.0
                    )
                )

                method = candidate.get(
                    "method",
                    ocr_result.get(
                        "method",
                        "unknown"
                    )
                )

                candidate_source = (
                    candidate.get(
                        "candidate_source",
                        "raw"
                    )
                )

                interpolated = bool(
                    candidate.get(
                        "interpolated",
                        False
                    )
                )

                observations[
                    track_id
                ].append(
                    {
                        "text":
                            text,

                        "confidence":
                            confidence,

                        "quality":
                            quality,

                        "sharpness":
                            sharpness,

                        "frame":
                            frame_number,

                        "plate_confidence":
                            plate_confidence,

                        "resolution":
                            resolution,

                        "method":
                            method,

                        "candidate_source":
                            candidate_source,

                        "interpolated":
                            interpolated
                    }
                )

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if frame_number % 300 == 0:

            print(
                f"Processed "
                f"{frame_number}/{frame_count} "
                f"frames..."
            )

    cap.release()

    # ========================================================
    # OCR COLLECTION COMPLETE
    # ========================================================

    print()
    print("=" * 75)
    print("OCR COLLECTION COMPLETE")
    print("=" * 75)
    print()

    # ========================================================
    # SAVE RAW OCR EVIDENCE
    # ========================================================

    observation_count = (
        save_ocr_observations(
            observations,
            ground_truth
        )
    )

    print(
        f"Saved {observation_count} "
        f"OCR observations to:"
    )

    print(
        f"  {OBSERVATION_CSV}"
    )

    # ========================================================
    # PRINT DIAGNOSTICS
    # ========================================================

    print_ocr_diagnostics(
        observations,
        ground_truth
    )

    # ========================================================
    # OUTPUT DIRECTORY
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

    # ========================================================
    # FINAL CONSENSUS
    # ========================================================

    for track_id in sorted(
        ground_truth
    ):

        actual = ground_truth[
            track_id
        ]

        track_observations = (
            observations.get(
                track_id,
                []
            )
        )

        seen_frames = (
            track_seen_frames.get(
                track_id,
                0
            )
        )

        plate_detections = (
            track_plate_detections.get(
                track_id,
                0
            )
        )

        print(
            f"Track {track_id}: "
            f"{len(track_observations)} "
            f"OCR observations"
        )

        print(
            f"  Track frames : "
            f"{seen_frames}"
        )

        print(
            f"  Plate detections : "
            f"{plate_detections}"
        )

        # ----------------------------------------------------
        # Consensus
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

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
                "track_id":
                    track_id,

                "actual_plate":
                    actual,

                "predicted_plate":
                    predicted,

                "exact_match":
                    exact,

                "character_accuracy":
                    round(
                        char_accuracy,
                        4
                    ),

                "edit_distance":
                    distance,

                "ocr_confidence":
                    round(
                        consensus_confidence,
                        4
                    ),

                "observation_count":
                    len(
                        track_observations
                    ),

                "consensus_count":
                    consensus_count,

                "track_frames":
                    seen_frames,

                "plate_detections":
                    plate_detections
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
                "consensus_count",
                "track_frames",
                "plate_detections"
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

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    tracked_count = sum(
        1
        for track_id in ground_truth
        if track_seen_frames.get(
            track_id,
            0
        ) > 0
    )

    plate_detected_count = sum(
        1
        for track_id in ground_truth
        if track_plate_detections.get(
            track_id,
            0
        ) > 0
    )

    readable_count = sum(
        1
        for track_id in ground_truth
        if len(
            observations.get(
                track_id,
                []
            )
        ) > 0
    )

    tracking_coverage = (
        tracked_count / total
        if total
        else 0.0
    )

    plate_detection_coverage = (
        plate_detected_count / total
        if total
        else 0.0
    )

    readable_coverage = (
        readable_count / total
        if total
        else 0.0
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("=" * 75)
    print("FINAL TEMPORAL BENCHMARK")
    print("=" * 75)

    print(
        f"Samples tested              : "
        f"{total}"
    )

    print(
        f"Vehicles tracked            : "
        f"{tracked_count}/{total} "
        f"({tracking_coverage:.1%})"
    )

    print(
        f"Vehicles with plate detect  : "
        f"{plate_detected_count}/{total} "
        f"({plate_detection_coverage:.1%})"
    )

    print(
        f"Vehicles with OCR evidence  : "
        f"{readable_count}/{total} "
        f"({readable_coverage:.1%})"
    )

    print(
        f"Exact recognitions          : "
        f"{exact_matches}/{total}"
    )

    print(
        f"Exact plate accuracy        : "
        f"{exact_accuracy:.1%}"
    )

    print(
        f"Character accuracy          : "
        f"{average_character_accuracy:.1%}"
    )

    print(
        f"Average edit distance       : "
        f"{average_edit_distance:.2f}"
    )

    print()

    print(
        f"Results saved to            : "
        f"{OUTPUT_CSV}"
    )

    print(
        f"OCR evidence saved to      : "
        f"{OBSERVATION_CSV}"
    )

    print("=" * 75)

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "This benchmark measures the current "
        "implementation on the available "
        "labeled video tracks."
    )

    print(
        "Track IDs are generated by ByteTrack "
        "during this benchmark run."
    )

    print(
        "A >90% result should only be claimed "
        "after sufficient labeled samples and "
        "representative conditions have been "
        "evaluated."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()