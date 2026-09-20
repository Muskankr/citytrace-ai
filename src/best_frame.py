def calculate_observation_score(
    detector_confidence: float,
    ocr_confidence: float,
    sharpness: float,
    resolution: float,
    format_score: float,
    valid: bool,
) -> float:
    """
    Calculate an overall quality score for an OCR observation.
    """

    sharpness_score = min(
        max(sharpness, 0.0) / 1000.0,
        1.0
    )

    resolution_score = min(
        max(resolution, 0.0) / 10000.0,
        1.0
    )

    detector_confidence = max(
        0.0,
        min(detector_confidence, 1.0)
    )

    ocr_confidence = max(
        0.0,
        min(ocr_confidence, 1.0)
    )

    format_score = max(
        0.0,
        min(format_score, 1.0)
    )

    score = (
        detector_confidence * 0.20
        + ocr_confidence * 0.30
        + sharpness_score * 0.15
        + resolution_score * 0.10
        + format_score * 0.15
        + (0.10 if valid else 0.0)
    )

    return min(score, 1.0)


def choose_best_observation(observations):
    """
    Select the strongest OCR observation.

    Each observation should contain:

        frame
        ocr_text
        ocr_confidence
        detector_confidence
        sharpness
        resolution
        format_score
        valid
    """

    if not observations:
        return None

    best = None
    best_score = -1.0

    for observation in observations:

        score = calculate_observation_score(
            detector_confidence=float(
                observation.get(
                    "detector_confidence",
                    0.0
                )
            ),

            ocr_confidence=float(
                observation.get(
                    "ocr_confidence",
                    0.0
                )
            ),

            sharpness=float(
                observation.get(
                    "sharpness",
                    0.0
                )
            ),

            resolution=float(
                observation.get(
                    "resolution",
                    0.0
                )
            ),

            format_score=float(
                observation.get(
                    "format_score",
                    0.0
                )
            ),

            valid=bool(
                observation.get(
                    "valid",
                    False
                )
            ),
        )

        observation["overall_score"] = score

        if score > best_score:

            best_score = score
            best = observation

    return best