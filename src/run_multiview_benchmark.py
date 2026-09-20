import os
import csv
import cv2

from rapidocr import RapidOCR

from src.ocr_correction import normalize_plate
from src.pipeline import run_ocr
from src.pipeline import choose_consensus


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

    for i, ca in enumerate(a, start=1):

        current = [i]

        for j, cb in enumerate(b, start=1):

            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (ca != cb)

            current.append(
                min(insert, delete, replace)
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
        1.0 - distance / max(
            len(actual),
            len(predicted)
        )
    )


def main():

    ground_truth = load_ground_truth()
    reader = RapidOCR()

    total = 0
    exact_matches = 0

    character_scores = []
    edit_distances = []

    print()
    print("=" * 70)
    print("MULTI-VIEW OCR BENCHMARK")
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
                f"Track {track_id}: IMAGE ERROR"
            )
            continue

        result = run_ocr(
            reader,
            image
        )

        if not result:
            print(
                f"Track {track_id}: UNREADABLE"
            )
            continue

        observations = []

        candidates = result.get(
            "candidates",
            []
        )

        # Use all OCR preprocessing observations
        for item in candidates:

            text = normalize_plate(
                item.get("text", "")
            )

            if not text:
                continue

            confidence = float(
                item.get("confidence", 0.0)
            )

            observations.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "quality": 1.0,
                    "format_score": 1.0,
                    "interpolated": False,
                }
            )

        if not observations:
            print(
                f"Track {track_id}: "
                f"NO OCR OBSERVATIONS"
            )
            continue

        consensus = choose_consensus(
            observations
        )

        if not consensus:
            print(
                f"Track {track_id}: "
                f"CONSENSUS FAILED"
            )
            continue

        predicted = normalize_plate(
            consensus["text"]
        )

        total += 1

        exact = (
            predicted == actual
            and bool(predicted)
        )

        if exact:
            exact_matches += 1

        char_score = character_accuracy(
            actual,
            predicted
        )

        distance = levenshtein_distance(
            actual,
            predicted
        )

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
            f"Predicted={predicted} | "
            f"Observations={len(observations)} | "
            f"OCR={consensus['confidence']:.3f} | "
            f"{status} | "
            f"Edit={distance} | "
            f"Character={char_score:.1%}"
        )

    print()
    print("-" * 70)

    if total == 0:
        print("No usable samples.")
        return

    exact_accuracy = (
        exact_matches / total
    )

    avg_character_accuracy = (
        sum(character_scores)
        / len(character_scores)
    )

    avg_edit_distance = (
        sum(edit_distances)
        / len(edit_distances)
    )

    print(
        f"Samples tested        : {total}"
    )

    print(
        f"Exact recognitions    : "
        f"{exact_matches}/{total}"
    )

    print(
        f"Exact plate accuracy  : "
        f"{exact_accuracy:.1%}"
    )

    print(
        f"Character accuracy    : "
        f"{avg_character_accuracy:.1%}"
    )

    print(
        f"Average edit distance : "
        f"{avg_edit_distance:.2f}"
    )

    print("-" * 70)

    print(
        "This benchmark uses multiple OCR "
        "observations from each saved plate crop."
    )

    print(
        "It is still a small benchmark and "
        "does not establish city-wide >90% accuracy."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()