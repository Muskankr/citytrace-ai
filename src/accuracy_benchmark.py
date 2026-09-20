import csv
import os

from src.ocr_correction import normalize_plate


GROUND_TRUTH = "data/benchmark/ground_truth.csv"


def load_ground_truth():
    records = {}

    with open(
        GROUND_TRUTH,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            track_id = row["track_id"].strip()
            actual = normalize_plate(
                row["actual_plate"]
            )

            records[track_id] = actual

    return records


def character_accuracy(actual, predicted):
    if not actual or not predicted:
        return 0.0

    length = min(
        len(actual),
        len(predicted)
    )

    matches = sum(
        1
        for i in range(length)
        if actual[i] == predicted[i]
    )

    return matches / max(
        len(actual),
        len(predicted)
    )


def evaluate(predictions):
    ground_truth = load_ground_truth()

    total = 0
    exact_matches = 0
    character_scores = []

    print()
    print("=" * 70)
    print("ANPR ACCURACY BENCHMARK")
    print("=" * 70)
    print()

    for track_id, actual in ground_truth.items():

        predicted = normalize_plate(
            predictions.get(track_id, "")
        )

        total += 1

        exact = (
            actual == predicted
            and bool(predicted)
        )

        if exact:
            exact_matches += 1

        char_score = character_accuracy(
            actual,
            predicted
        )

        character_scores.append(
            char_score
        )

        status = "CORRECT" if exact else "WRONG"

        print(
            f"Track {track_id}: "
            f"Actual={actual} | "
            f"Predicted={predicted or 'UNREADABLE'} | "
            f"{status} | "
            f"Character={char_score:.1%}"
        )

    if total == 0:
        print("No benchmark samples found.")
        return

    exact_accuracy = (
        exact_matches / total
    )

    average_character_accuracy = (
        sum(character_scores)
        / len(character_scores)
    )

    print()
    print("-" * 70)
    print(
        f"Exact plate accuracy : "
        f"{exact_accuracy:.1%}"
    )

    print(
        f"Character accuracy   : "
        f"{average_character_accuracy:.1%}"
    )

    print(
        f"Correct plates       : "
        f"{exact_matches}/{total}"
    )

    print("-" * 70)

    if exact_accuracy >= 0.90:
        print(
            "Benchmark result: "
            "90%+ exact recognition on this dataset"
        )
    else:
        print(
            "Benchmark result: "
            "Below 90% on this dataset"
        )

    print("=" * 70)


if __name__ == "__main__":

    # Temporary predictions from our
    # already verified OCR experiments.
    predictions = {
        "86": "EF10DZT",
        "95": "EY09VNS",
    }

    evaluate(predictions)