import os
import csv
import cv2

from rapidocr import RapidOCR

from src.pipeline import run_ocr, choose_consensus
from src.ocr_correction import normalize_plate
from src.temporal_interpolation import interpolate_plate_observations


GROUND_TRUTH = "data/benchmark/ground_truth.csv"
PLATE_DIR = "outputs/pipeline_plates"


def load_ground_truth():
    records = {}

    with open(GROUND_TRUTH, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            track_id = row["track_id"].strip()
            actual = normalize_plate(row["actual_plate"])
            records[track_id] = actual

    return records


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
            substitution = previous[j - 1] + (char_a != char_b)

            current.append(
                min(insertion, deletion, substitution)
            )

        previous = current

    return previous[-1]


def character_accuracy(actual, predicted):
    if not actual or not predicted:
        return 0.0

    distance = levenshtein_distance(actual, predicted)

    return max(
        0.0,
        1.0 - (distance / max(len(actual), len(predicted)))
    )


def build_observations(reader, image):
    result = run_ocr(reader, image)

    if not result:
        return []

    candidates = result.get("candidates", [])

    if not candidates:
        candidates = [
            {
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "method": result.get("method", "unknown"),
            }
        ]

    observations = []

    for candidate in candidates:

        text = normalize_plate(
            candidate.get("text", "")
        )

        if not text:
            continue

        observations.append(
            {
                "text": text,
                "confidence": float(
                    candidate.get("confidence", 0.0)
                ),
                "quality": 0.8,
                "sharpness": 1.0,
                "frame": 0,
                "plate_confidence": 1.0,
                "interpolated": False,
            }
        )

    return observations


def main():

    ground_truth = load_ground_truth()

    reader = RapidOCR()

    total = 0
    exact_matches = 0

    character_scores = []
    edit_distances = []

    print()
    print("=" * 70)
    print("TEMPORAL OCR BENCHMARK")
    print("=" * 70)
    print()

    for track_id, actual in ground_truth.items():

        image_path = os.path.join(
            PLATE_DIR,
            f"track_{track_id}.jpg"
        )

        if not os.path.exists(image_path):
            print(
                f"Track {track_id}: IMAGE NOT FOUND"
            )
            continue

        image = cv2.imread(image_path)

        if image is None:
            print(
                f"Track {track_id}: IMAGE COULD NOT BE READ"
            )
            continue

        observations = build_observations(
            reader,
            image
        )

        if not observations:
            print(
                f"Track {track_id}: NO OCR OBSERVATIONS"
            )
            continue

        consensus = choose_consensus(
            observations
        )

        if not consensus:
            predicted = ""
            confidence = 0.0
        else:
            predicted = normalize_plate(
                consensus.get("text", "")
            )

            confidence = float(
                consensus.get("confidence", 0.0)
            )

        exact = (
            bool(predicted)
            and predicted == actual
        )

        distance = levenshtein_distance(
            actual,
            predicted
        )

        char_score = character_accuracy(
            actual,
            predicted
        )

        total += 1

        if exact:
            exact_matches += 1

        character_scores.append(
            char_score
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
            f"Track {track_id}: "
            f"Actual={actual} | "
            f"Predicted={predicted or 'UNREADABLE'} | "
            f"Consensus OCR={confidence:.3f} | "
            f"{status} | "
            f"Edit distance={distance} | "
            f"Character={char_score:.1%}"
        )

    print()
    print("-" * 70)

    if total == 0:
        print("No usable benchmark samples.")
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

    print(
        f"Samples tested             : {total}"
    )

    print(
        f"Exact recognitions         : "
        f"{exact_matches}/{total}"
    )

    print(
        f"Exact plate accuracy       : "
        f"{exact_accuracy:.1%}"
    )

    print(
        f"Character accuracy        : "
        f"{average_character_accuracy:.1%}"
    )

    print(
        f"Average edit distance     : "
        f"{average_edit_distance:.2f}"
    )

    print("-" * 70)

    print(
        "NOTE: This benchmark evaluates "
        "the current consensus logic on "
        "the available benchmark crops."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()