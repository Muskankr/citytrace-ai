import os
import csv
import cv2
from rapidocr import RapidOCR

from src.pipeline import run_ocr
from src.ocr_correction import (
    normalize_plate,
    corrected_candidates,
    plate_format_score,
)


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
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (char_a != char_b)

            current.append(
                min(insert_cost, delete_cost, replace_cost)
            )

        previous = current

    return previous[-1]


def character_accuracy(actual, predicted):
    if not actual or not predicted:
        return 0.0

    distance = levenshtein_distance(actual, predicted)

    return max(
        0.0,
        1.0 - distance / max(len(actual), len(predicted))
    )


def candidate_score(candidate, original_text, ocr_confidence):
    """
    Conservative candidate scoring.

    Prefer the original OCR result when it already has:
    - good OCR confidence
    - valid plate structure

    Corrections should only win when they provide
    a meaningful structural improvement.
    """

    format_score = plate_format_score(candidate)

    original_format_score = plate_format_score(original_text)

    length_score = 1.0 if 7 <= len(candidate) <= 10 else 0.0

    structure_score = 0.0

    if len(candidate) >= 4:

        if candidate[:2].isalpha():
            structure_score += 0.4

        if candidate[2:4].isdigit():
            structure_score += 0.6

    # Base candidate score
    score = (
        0.40 * ocr_confidence
        + 0.30 * format_score
        + 0.20 * structure_score
        + 0.10 * length_score
    )

    # IMPORTANT:
    # If candidate is exactly the original OCR,
    # give it a small preference.
    if candidate == original_text:
        score += 0.12

    # If original OCR is already a perfect-format plate,
    # don't aggressively change it.
    if (
        candidate != original_text
        and original_format_score == 1.0
        and format_score == 1.0
    ):
        score -= 0.08

    return score


def choose_best_candidate(result):
    if not result:
        return None, 0.0

    raw_text = normalize_plate(result.get("text", ""))
    raw_confidence = float(result.get("confidence", 0.0))

    if not raw_text:
        return None, 0.0

    candidates = []

    # Use every OCR candidate produced by run_ocr()
    raw_candidates = result.get("candidates", [])

    if not raw_candidates:
        raw_candidates = [
            {
                "text": raw_text,
                "confidence": raw_confidence,
            }
        ]

    for item in raw_candidates:

        text = normalize_plate(item.get("text", ""))

        if not text:
            continue

        confidence = float(
            item.get("confidence", raw_confidence)
        )

        generated = corrected_candidates(text)

        for candidate in generated:

            candidate = normalize_plate(candidate)

            if not candidate:
                continue

            score = candidate_score(
    candidate,
    raw_text,
    confidence
)

            candidates.append(
                {
                    "text": candidate,
                    "ocr_confidence": confidence,
                    "score": score,
                }
            )

    if not candidates:
        return raw_text, raw_confidence

    # Remove duplicate candidates while keeping best score
    best_by_text = {}

    for item in candidates:

        text = item["text"]

        if (
            text not in best_by_text
            or item["score"] > best_by_text[text]["score"]
        ):
            best_by_text[text] = item

    candidates = list(best_by_text.values())

    best = max(
        candidates,
        key=lambda item: item["score"]
    )

    return best["text"], best["ocr_confidence"]


def main():

    ground_truth = load_ground_truth()

    reader = RapidOCR()

    total = 0
    exact_matches = 0

    character_scores = []
    edit_distances = []

    print()
    print("=" * 70)
    print("OCR CANDIDATE-SELECTION BENCHMARK")
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

        result = run_ocr(reader, image)

        predicted, confidence = choose_best_candidate(result)

        total += 1

        exact = (
            predicted == actual
            and bool(predicted)
        )

        if exact:
            exact_matches += 1

        char_score = character_accuracy(
            actual,
            predicted or ""
        )

        distance = levenshtein_distance(
            actual,
            predicted or ""
        )

        character_scores.append(char_score)
        edit_distances.append(distance)

        status = "CORRECT" if exact else "WRONG"

        print(
            f"Track {track_id}: "
            f"Actual={actual} | "
            f"Predicted={predicted or 'UNREADABLE'} | "
            f"OCR={confidence:.3f} | "
            f"{status} | "
            f"Edit={distance} | "
            f"Character={char_score:.1%}"
        )

    print()
    print("-" * 70)

    if total == 0:
        print("No usable benchmark samples.")
        return

    exact_accuracy = exact_matches / total

    average_character_accuracy = (
        sum(character_scores)
        / len(character_scores)
    )

    average_edit_distance = (
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
        f"{average_character_accuracy:.1%}"
    )

    print(
        f"Average edit distance : "
        f"{average_edit_distance:.2f}"
    )

    print("-" * 70)

    print(
        "NOTE: This is a small 12-sample benchmark."
    )

    print(
        "Candidate generation is evaluated here, "
        "but this is not evidence of city-wide >90% accuracy."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()