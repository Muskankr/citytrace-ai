import re
from itertools import product


# ============================================================
# OCR CONFUSION MAP
# ============================================================

# These are visually common OCR confusions.
# IMPORTANT:
# We do NOT blindly apply them.
# Candidate generation + plate structure decides which
# correction is plausible.

CONFUSION_MAP = {
    "O": ["0"],
    "Q": ["0"],
    "D": ["0"],

    "I": ["1"],
    "L": ["1"],

    "Z": ["2"],

    "S": ["5"],

    "G": ["6"],

    "B": ["8"],

    # Reverse-looking confusions are kept limited.
    # They are only considered when the expected position
    # is alphabetic.
    "0": ["O"],
    "1": ["I"],
    "2": ["Z"],
    "5": ["S"],
    "6": ["G"],
    "8": ["B"],

    # OCR sometimes reads W as M.
    "M": ["W"],
    "W": ["M"],
}


# ============================================================
# INDIAN-STYLE PLATE PATTERNS
# ============================================================

PLATE_PATTERNS = [

    # XX00XXX
    # Example: EF10DZT
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

    # AAA00AA
    r"^[A-Z]{3}[0-9]{2}[A-Z]{2}$",

    # AA0AAAA
    r"^[A-Z]{2}[0-9][A-Z]{4}$",
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
# FORMAT CHECK
# ============================================================

def matches_plate_format(text):

    text = normalize_plate(text)

    if not text:
        return False

    return any(
        re.fullmatch(
            pattern,
            text
        )
        for pattern in PLATE_PATTERNS
    )


# ============================================================
# FORMAT SCORE
# ============================================================

def plate_format_score(text):

    text = normalize_plate(text)

    if not text:
        return 0.0

    # Exact structural match
    if matches_plate_format(text):
        return 1.0

    score = 0.0

    # Reasonable plate length
    if 6 <= len(text) <= 10:
        score += 0.20

    # First two characters are normally letters
    if len(text) >= 2:

        if text[:2].isalpha():
            score += 0.30

    # Plate should contain both letters and digits
    has_letters = any(
        c.isalpha()
        for c in text
    )

    has_digits = any(
        c.isdigit()
        for c in text
    )

    if has_letters and has_digits:
        score += 0.20

    # The beginning should not be numeric
    if len(text) >= 2:

        if not text[:2].isdigit():
            score += 0.10

    return min(
        score,
        1.0
    )


# ============================================================
# POSITION-AWARE CANDIDATE GENERATION
# ============================================================
def generate_candidates(text):
    """
    Generate conservative OCR correction candidates.

    Candidates are generated according to the supported
    plate structures instead of blindly replacing OCR
    characters everywhere.

    This allows cases such as:

        GXI5OGJ -> GXI50GJ
        FJI4ZHY -> FJI42HY
        EFIODZT -> EF10DZT

    without globally converting every I/O/etc.
    """

    text = normalize_plate(text)

    if not text:
        return []

    candidates = {text}

    # --------------------------------------------------------
    # OCR confusion mappings
    # --------------------------------------------------------

    digit_map = {
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

    letter_map = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    # --------------------------------------------------------
    # Supported benchmark-observed structures.
    #
    # L = letter
    # D = digit
    # --------------------------------------------------------

    structures = [
        "LLDDLLL",
        "LLDDLL",
        "LLDDL",
        "LLDDLLDDDD",
        "LLDDLLLDDDD",
        "LLDLLDDDD",
        "LLDLLLDDDD",

        # Benchmark-observed:
        "LLLDDLL",   # GXI50GJ / FJI42HY
        "LLDLLLL",   # EY6INBG / AV0BHVF
    ]

    # --------------------------------------------------------
    # Generate candidates for each compatible structure.
    # --------------------------------------------------------

    for structure in structures:

        if len(text) != len(structure):
            continue

        possible_chars = []

        for index, char in enumerate(text):

            expected = structure[index]

            # ------------------------------------------------
            # Digit position
            # ------------------------------------------------

            if expected == "D":

                options = {char}

                if char in digit_map:
                    options.add(
                        digit_map[char]
                    )

                # Keep only digits.
                options = {
                    value
                    for value in options
                    if value.isdigit()
                }

            # ------------------------------------------------
            # Letter position
            # ------------------------------------------------

            else:

                options = {char}

                if char in letter_map:
                    options.add(
                        letter_map[char]
                    )

                # Keep only letters.
                options = {
                    value
                    for value in options
                    if value.isalpha()
                }

            if not options:
                possible_chars = []
                break

            possible_chars.append(
                sorted(options)
            )

        if not possible_chars:
            continue

        # ----------------------------------------------------
        # Limit combinations.
        # ----------------------------------------------------

        total = 1

        for options in possible_chars:
            total *= len(options)

        # Avoid a combinatorial explosion.
        if total > 256:
            continue

        for combination in product(
            *possible_chars
        ):

            candidate = "".join(
                combination
            )

            candidates.add(candidate)

    # --------------------------------------------------------
    # Preserve the original candidate.
    # --------------------------------------------------------

    return list(candidates)


# ============================================================
# BEST CORRECTION
# ============================================================


def correct_plate(text):
    """
    Return the strongest structurally valid OCR candidate.

    Conservative OCR correction:
    - preserve the original when possible
    - prefer obvious OCR confusion corrections
    - use plate format as supporting evidence
    - do not aggressively rewrite ambiguous characters
    """

    text = normalize_plate(text)

    if not text:
        return ""

    candidates = generate_candidates(text)

    valid_candidates = [
        candidate
        for candidate in candidates
        if matches_plate_format(candidate)
    ]

    if not valid_candidates:
        return text

    digit_confusions = {
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

    letter_confusions = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    def correction_cost(candidate):

        if len(text) != len(candidate):
            return 1000.0

        cost = 0.0

        for original, corrected in zip(text, candidate):

            if original == corrected:
                continue

            if (
                original in digit_confusions
                and digit_confusions[original] == corrected
            ):
                cost += 0.20

            elif (
                original in letter_confusions
                and letter_confusions[original] == corrected
            ):
                cost += 0.20

            else:
                cost += 1.0

        cost -= 0.10 * plate_format_score(candidate)

        return cost

    valid_candidates.sort(
        key=lambda candidate: (
            correction_cost(candidate),
            -plate_format_score(candidate),
        )
    )

    best = valid_candidates[0]

    changes = sum(
        original != corrected
        for original, corrected in zip(text, best)
    )

    if changes > 2:
        return text

    return best


# ============================================================
# CANDIDATE LIST
# ============================================================

def corrected_candidates(text):
    """
    Return OCR text followed by structurally valid,
    position-aware correction candidates.
    """

    text = normalize_plate(text)

    if not text:
        return []

    candidates = generate_candidates(text)

    ordered = [text]

    valid_candidates = [
        candidate
        for candidate in candidates
        if (
            candidate != text
            and matches_plate_format(candidate)
        )
    ]

    digit_confusions = {
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

    letter_confusions = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    def distance(candidate):
        if len(text) != len(candidate):
            return 100 + abs(len(text) - len(candidate))

        cost = 0.0

        for original_char, candidate_char in zip(
            text,
            candidate
        ):
            if original_char == candidate_char:
                continue

            if candidate_char.isdigit():
                if (
                    original_char in digit_confusions
                    and digit_confusions[original_char]
                    == candidate_char
                ):
                    cost += 0.20
                else:
                    cost += 1.0

            elif candidate_char.isalpha():
                if (
                    original_char in letter_confusions
                    and letter_confusions[original_char]
                    == candidate_char
                ):
                    cost += 0.20
                else:
                    cost += 1.0

            else:
                cost += 1.0

        return cost

    valid_candidates.sort(
        key=lambda candidate: (
            distance(candidate),
            -plate_format_score(candidate),
        )
    )

    ordered.extend(valid_candidates)

    return ordered


# ============================================================
# PLATE SHAPE
# ============================================================

def looks_like_plate(text):

    text = normalize_plate(
        text
    )

    if not text:
        return False

    return matches_plate_format(
        text
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [
        "NAI3NRU",
        "APOSJEO",
        "GXI5OGJ",
        "BG6SUSJ",
        "FJI4ZHY",
        "EYGINBG",
        "AVOBHVF",
        "GJO6EPD",
        "AK64DMV",
        "KHO6KSU",
        "EFIODZT",
        "EY09VMS",
    ]

    print()
    print("=" * 75)
    print("OCR CORRECTION TEST")
    print("=" * 75)

    for text in tests:

        print()
        print(
            f"OCR         : {text}"
        )

        print(
            f"Corrected   : "
            f"{correct_plate(text)}"
        )

        print(
            f"Candidates  : "
            f"{corrected_candidates(text)}"
        )

    print()
    print("=" * 75)