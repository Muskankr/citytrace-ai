import re


# ============================================================
# CHARACTER CORRECTIONS
# ============================================================

DIGIT_CORRECTIONS = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "B": "8",
}


# ============================================================
# INDIAN-STYLE PLATE PATTERNS
# ============================================================

PLATE_PATTERNS = [
    # XX00XXX
    r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$",

    # XX00XX
    r"^[A-Z]{2}[0-9]{2}[A-Z]{2}$",

    # XX00X0-0000
    r"^[A-Z]{2}[0-9]{2}[A-Z][0-9]{1,4}$",

    # XX00XX0-0000
    r"^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{1,4}$",

    # XX00XXX0-0000
    r"^[A-Z]{2}[0-9]{2}[A-Z]{3}[0-9]{1,4}$",

    # XX0X0-0000
    r"^[A-Z]{2}[0-9][A-Z][0-9]{1,4}$",

    # XX0XX0-0000
    r"^[A-Z]{2}[0-9][A-Z]{2}[0-9]{1,4}$",

    # XX0XXX0-0000
    r"^[A-Z]{2}[0-9][A-Z]{3}[0-9]{1,4}$",
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_plate(text):
    if not text:
        return ""

    text = str(text).upper()

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


# ============================================================
# POSITION-AWARE DIGIT CORRECTION
# ============================================================

def correct_digit(char):
    return DIGIT_CORRECTIONS.get(
        char,
        char
    )


def correct_plate(text):
    """
    Conservative correction.

    Only applies character substitutions to positions
    that are expected to contain digits for the common
    Indian plate structures.

    It does NOT blindly modify alphabetic positions.
    """

    text = normalize_plate(text)

    if not text:
        return ""

    chars = list(text)

    # Common Indian structure:
    # XX00...
    #
    # Position 2 and 3 are normally digits.
    if len(chars) >= 4:

        chars[2] = correct_digit(
            chars[2]
        )

        chars[3] = correct_digit(
            chars[3]
        )

    return "".join(chars)


# ============================================================
# FORMAT SCORE
# ============================================================

def plate_format_score(text):
    """
    Score how closely OCR text matches supported
    Indian-style registration structures.

    1.00 = exact supported structure
    0.45 = partially plausible
    0.00 = clearly invalid
    """

    text = normalize_plate(text)

    if not text:
        return 0.0

    # Exact supported format
    for pattern in PLATE_PATTERNS:

        if re.fullmatch(
            pattern,
            text
        ):
            return 1.0

    score = 0.0

    # Length plausibility
    if 6 <= len(text) <= 10:
        score += 0.20

    # First two characters normally state/region letters
    if len(text) >= 2:

        if text[:2].isalpha():
            score += 0.25

    # Mixture of letters and digits
    has_letters = any(
        char.isalpha()
        for char in text
    )

    has_digits = any(
        char.isdigit()
        for char in text
    )

    if has_letters and has_digits:
        score += 0.20

    # First two characters should not be digits
    if len(text) >= 2:

        if not text[:2].isdigit():
            score += 0.10

    return min(
        score,
        1.0
    )


# ============================================================
# CANDIDATE GENERATION
# ============================================================

def corrected_candidates(text):

    text = normalize_plate(text)

    if not text:
        return []

    candidates = [
        text
    ]

    corrected = correct_plate(
        text
    )

    if (
        corrected
        and corrected not in candidates
    ):
        candidates.append(
            corrected
        )

    return candidates


# ============================================================
# PLATE SHAPE
# ============================================================

def looks_like_plate(text):

    text = normalize_plate(
        text
    )

    if not text:
        return False

    return any(
        re.fullmatch(
            pattern,
            text
        )
        for pattern in PLATE_PATTERNS
    )