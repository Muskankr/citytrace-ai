from collections import defaultdict
from typing import List, Tuple


def character_consensus(
    observations: List[Tuple[str, float]]
) -> str:
    """
    Find the most reliable character at each position.

    observations:
        [
            ("EY09VNS", 0.91),
            ("EY09VNS", 0.89),
            ("EY09VYS", 0.81),
        ]

    Returns the consensus plate.
    """

    if not observations:
        return ""

    # Keep only reasonably useful OCR results
    observations = [
        (text, score)
        for text, score in observations
        if text and len(text) == 7
    ]

    if not observations:
        return ""

    result = []

    for position in range(7):

        scores = defaultdict(float)

        for text, confidence in observations:
            char = text[position]

            # Weight each character by OCR confidence
            scores[char] += confidence

        if scores:
            best_char = max(scores, key=scores.get)
            result.append(best_char)

    return "".join(result)


def plate_consensus(
    observations: List[Tuple[str, float]]
) -> str:
    """
    Calculate consensus and then apply
    position-aware correction.
    """

    from src.ocr_correction import correct_plate

    consensus = character_consensus(observations)

    return correct_plate(consensus)