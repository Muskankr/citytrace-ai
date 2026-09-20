import re


# Common OCR confusions
DIGIT_CORRECTIONS = {
    "O": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "B": "8",
}


def correct_numeric_position(char):
    """
    Convert common OCR mistakes into digits
    when the position is expected to contain a digit.
    """
    return DIGIT_CORRECTIONS.get(char, char)


def correct_plate(text):
    """
    Conservative position-aware correction
    for common Indian plate OCR errors.
    """

    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)

    if len(text) != 7:
        return text

    chars = list(text)

    # -------------------------------------------------
    # 7-character pattern:
    #
    # AA00AAA
    #
    # Example:
    # EF10DZT
    # EY09VWS
    # -------------------------------------------------

    # State code: positions 0-1 -> letters
    # Do not modify these.

    # RTO/district: positions 2-3 -> digits
    chars[2] = correct_numeric_position(chars[2])
    chars[3] = correct_numeric_position(chars[3])

    # Series: positions 4-6 -> letters
    # Do not blindly change letters.

    return "".join(chars)


tests = [
    ("EY09VNS", "EY09VWS"),
    ("EFIODZT", "EF10DZT"),
    ("EY09VYS", "EY09VYS"),
    ("EF1OOZT", "EF100ZT"),
]


print("=" * 60)
print("POSITION-AWARE PLATE CORRECTION TEST")
print("=" * 60)

for original, expected in tests:
    corrected = correct_plate(original)

    print(f"\nOCR       : {original}")
    print(f"Corrected : {corrected}")
    print(f"Expected  : {expected}")

    if corrected == expected:
        print("✅ Correct")
    else:
        print("⚠️ Needs temporal/context correction")