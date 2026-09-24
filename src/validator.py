import re

from src.ocr_correction import (
    normalize_plate,
    correct_plate,
    plate_format_score,
)


# ============================================================
# INDIAN PLATE STRUCTURAL PATTERNS
# ============================================================

PLATE_PATTERNS = [

    r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$",
    r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$",
    r"^[A-Z]{2}[0-9]{2}[A-Z][0-9]{1,4}$",
    r"^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{1,4}$",
    r"^[A-Z]{2}[0-9]{2}[A-Z]{3}[0-9]{1,4}$",
    r"^[A-Z]{2}[0-9][A-Z][0-9]{1,4}$",
    r"^[A-Z]{2}[0-9][A-Z]{2}[0-9]{1,4}$",
    r"^[A-Z]{2}[0-9][A-Z]{3}[0-9]{1,4}$",

    # Benchmark-observed structures
    r"^[A-Z]{3}[0-9]{2}[A-Z]{2}$",
    r"^[A-Z]{2}[0-9][A-Z]{4}$",
]


# ============================================================
# CLEAN
# ============================================================

def clean_plate(text):
    """Normalize OCR output."""

    return normalize_plate(text)


# ============================================================
# STRUCTURAL VALIDATION
# ============================================================

def is_possible_indian_plate(text):
    """
    Check whether OCR text resembles an Indian
    registration-number structure.

    This is structural validation only.
    It does NOT verify the registration against
    a government database.
    """

    text = clean_plate(text)

    if not 6 <= len(text) <= 10:
        return False

    for pattern in PLATE_PATTERNS:

        # Support both compiled regex patterns
        # and normal string patterns.
        if hasattr(pattern, "fullmatch"):
            matched = pattern.fullmatch(text)
        else:
            matched = re.fullmatch(pattern, text)

        if matched:
            return True

    return False


# ============================================================
# VALIDATE
# ============================================================

def validate_plate(text, confidence=0.0):

    cleaned = clean_plate(text)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    # --------------------------------------------------------
    # EMPTY
    # --------------------------------------------------------

    if not cleaned:

        return {
            "plate_number": None,
            "confidence": confidence,
            "format_score": 0.0,
            "valid": False,
            "status": "UNREADABLE",
        }

    # --------------------------------------------------------
    # TEST ORIGINAL + CORRECTED
    # --------------------------------------------------------

    candidates = []

    candidates.append(
        cleaned
    )

    corrected = correct_plate(
        cleaned
    )

    if (
        corrected
        and corrected not in candidates
    ):
        candidates.append(
            corrected
        )

    # --------------------------------------------------------
    # FIND BEST STRUCTURAL CANDIDATE
    # --------------------------------------------------------

    best_candidate = None
    best_format_score = 0.0
    best_is_valid_shape = False

    for candidate in candidates:

        score = plate_format_score(
            candidate
        )

        valid_shape = (
            is_possible_indian_plate(
                candidate
            )
        )

        if (
            valid_shape
            and (
                not best_is_valid_shape
                or score > best_format_score
            )
        ):

            best_candidate = candidate
            best_format_score = score
            best_is_valid_shape = True

    # --------------------------------------------------------
    # VALID STRUCTURE FOUND
    # --------------------------------------------------------

    if best_candidate:

        if confidence >= 0.70:

            return {
                "plate_number": best_candidate,
                "confidence": confidence,
                "format_score": best_format_score,
                "valid": True,
                "status": "VALID",
            }

        if confidence >= 0.50:

            return {
                "plate_number": best_candidate,
                "confidence": confidence,
                "format_score": best_format_score,
                "valid": False,
                "status": "LOW_CONFIDENCE",
            }

        return {
            "plate_number": best_candidate,
            "confidence": confidence,
            "format_score": best_format_score,
            "valid": False,
            "status": "REVIEW_REQUIRED",
        }

    # --------------------------------------------------------
    # NO VALID STRUCTURE
    # --------------------------------------------------------

    return {
        "plate_number": None,
        "confidence": confidence,
        "format_score": plate_format_score(cleaned),
        "valid": False,
        "status": "INVALID_FORMAT",
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_cases = [

        # Standard examples
        ("HR26AB1234", 0.92),
        ("DL01CA1234", 0.84),
        ("UP16AB1234", 0.76),

        # Actual OCR examples from our video
        ("EFIODZT", 0.93),
        ("EY09VWS", 0.89),
        ("AP05JEO", 0.98),
        ("GJ05EPD", 0.94),
        ("DA07CLX", 0.96),
        ("BP63LYH", 0.99),
        ("CE61NYL", 0.96),

        # Poor OCR
        ("50WNA", 0.77),
        ("27", 0.46),
        ("O", 0.36),
        ("IM", 0.53),
        ("", 0.00),
    ]

    print()
    print("=" * 70)
    print("INDIAN PLATE VALIDATOR TEST")
    print("=" * 70)

    for text, confidence in test_cases:

        result = validate_plate(
            text,
            confidence
        )

        print()
        print(f"OCR        : {text}")
        print(f"Confidence : {confidence}")
        print(f"Result     : {result}")

    print()
    print("=" * 70)