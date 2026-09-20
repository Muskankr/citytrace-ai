import os
import re
import cv2
import easyocr
import numpy as np


# ==========================================
# CONFIGURATION
# ==========================================

PLATE_FOLDER = "outputs/plates"

ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


# ==========================================
# CLEAN OCR TEXT
# ==========================================

def clean_text(text):
    """
    Convert OCR result into clean A-Z / 0-9 text.
    """

    text = text.upper()

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


# ==========================================
# INDIAN PLATE FORMAT
# ==========================================

def looks_like_plate(text):
    """
    Basic Indian registration plate pattern.

    Examples:
    HR26AB1234
    DL01CA1234
    UP16AB1234
    MH12XY5678
    """

    pattern = (
        r"^[A-Z]{2}"
        r"[0-9]{1,2}"
        r"[A-Z]{1,3}"
        r"[0-9]{1,4}$"
    )

    return bool(
        re.fullmatch(pattern, text)
    )


# ==========================================
# PREPROCESSING
# ==========================================

def preprocess_variants(image):

    # --------------------------------------
    # Original
    # --------------------------------------

    original = image.copy()

    # --------------------------------------
    # Resize
    # --------------------------------------

    resized = cv2.resize(
        image,
        None,
        fx=6,
        fy=6,
        interpolation=cv2.INTER_CUBIC
    )

    # --------------------------------------
    # Grayscale
    # --------------------------------------

    gray = cv2.cvtColor(
        resized,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------
    # CLAHE
    # --------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # --------------------------------------
    # Bilateral filtering
    # --------------------------------------

    denoised = cv2.bilateralFilter(
        enhanced,
        9,
        75,
        75
    )

    # --------------------------------------
    # Sharpen
    # --------------------------------------

    sharpen_kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    sharpened = cv2.filter2D(
        denoised,
        -1,
        sharpen_kernel
    )

    # --------------------------------------
    # OTSU threshold
    # --------------------------------------

    otsu = cv2.threshold(
        sharpened,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # --------------------------------------
    # Adaptive threshold
    # --------------------------------------

    adaptive = cv2.adaptiveThreshold(
        sharpened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5
    )

    return [
        ("original", original),
        ("resized", resized),
        ("gray", gray),
        ("clahe", enhanced),
        ("sharpened", sharpened),
        ("otsu", otsu),
        ("adaptive", adaptive)
    ]


# ==========================================
# CANDIDATE SCORE
# ==========================================

def candidate_score(text, confidence, count):
    """
    Give additional weight to:
    - valid Indian plate format
    - reasonable length
    - repeated OCR result
    """

    score = float(confidence)

    # Strong bonus for valid plate format
    if looks_like_plate(text):
        score += 0.50

    # Reasonable registration plate length
    if 7 <= len(text) <= 10:
        score += 0.15

    # Repeated detection across preprocessing variants
    score += min(count * 0.05, 0.20)

    return score


# ==========================================
# OCR ONE IMAGE
# ==========================================

def process_plate(reader, filename):

    image_path = os.path.join(
        PLATE_FOLDER,
        filename
    )

    image = cv2.imread(
        image_path
    )

    if image is None:
        return None

    variants = preprocess_variants(
        image
    )

    candidates = []

    # --------------------------------------
    # Run OCR on every variant
    # --------------------------------------

    for variant_name, variant in variants:

        results = reader.readtext(
            variant,
            detail=1,
            paragraph=False,
            allowlist=ALLOWLIST,
            text_threshold=0.4,
            low_text=0.2,
            link_threshold=0.2
        )

        for detection in results:

            bbox, text, confidence = detection

            text = clean_text(text)

            confidence = float(confidence)

            if not text:
                continue

            # Ignore extremely tiny OCR results
            if len(text) < 2:
                continue

            candidates.append({
                "text": text,
                "confidence": confidence,
                "variant": variant_name
            })

    # --------------------------------------
    # Nothing detected
    # --------------------------------------

    if not candidates:

        return {
            "filename": filename,
            "text": "UNKNOWN",
            "confidence": 0.0,
            "valid": False,
            "status": "UNREADABLE",
            "count": 0
        }

    # --------------------------------------
    # Count repeated OCR strings
    # --------------------------------------

    text_counts = {}

    for candidate in candidates:

        text = candidate["text"]

        text_counts[text] = (
            text_counts.get(text, 0) + 1
        )

    # --------------------------------------
    # Score candidates
    # --------------------------------------

    scored_candidates = []

    for candidate in candidates:

        text = candidate["text"]
        confidence = candidate["confidence"]

        count = text_counts[text]

        score = candidate_score(
            text,
            confidence,
            count
        )

        scored_candidates.append({
            "text": text,
            "confidence": confidence,
            "score": score,
            "count": count,
            "variant": candidate["variant"]
        })

    # Highest overall score
    scored_candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = scored_candidates[0]

    best_text = best["text"]
    best_confidence = best["confidence"]
    repeat_count = best["count"]

    valid = looks_like_plate(
        best_text
    )

    # --------------------------------------
    # Status
    # --------------------------------------

    if valid and best_confidence >= 0.70:
        status = "VALID / HIGH CONFIDENCE"

    elif valid:
        status = "POSSIBLE PLATE"

    elif best_confidence >= 0.60:
        status = "OCR TEXT / FORMAT UNCERTAIN"

    else:
        status = "UNREADABLE / LOW CONFIDENCE"

    return {
        "filename": filename,
        "text": best_text,
        "confidence": best_confidence,
        "valid": valid,
        "status": status,
        "count": repeat_count,
        "variant": best["variant"],
        "all_candidates": scored_candidates
    }


# ==========================================
# MAIN
# ==========================================

def main():

    print()
    print("==========================================")
    print("       AI ANPR - OCR ENGINE")
    print("==========================================")
    print()

    print("Loading EasyOCR...")

    reader = easyocr.Reader(
        ["en"],
        gpu=False
    )

    # --------------------------------------
    # Check folder
    # --------------------------------------

    if not os.path.exists(PLATE_FOLDER):

        print(
            f"❌ Plate folder not found: "
            f"{PLATE_FOLDER}"
        )

        return

    # --------------------------------------
    # Find images
    # --------------------------------------

    files = [
        f
        for f in os.listdir(PLATE_FOLDER)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
    ]

    files.sort()

    if not files:

        print("❌ No plate images found.")

        return

    print(
        f"Found {len(files)} plate images"
    )

    print()
    print(
        "Running OCR with multiple "
        "preprocessing variants..."
    )
    print()

    print("=" * 100)

    results = []

    # --------------------------------------
    # Process all plates
    # --------------------------------------

    for filename in files:

        result = process_plate(
            reader,
            filename
        )

        if result is None:
            continue

        results.append(result)

        print(
            f"{filename:<25} "
            f"TEXT: {result['text']:<15} "
            f"CONF: {result['confidence']:.2f}   "
            f"REPEAT: {result['count']}   "
            f"[{result['status']}]"
        )

    print("=" * 100)

    # ======================================
    # SUMMARY
    # ======================================

    valid_count = sum(
        1
        for r in results
        if r["valid"]
    )

    high_confidence_count = sum(
        1
        for r in results
        if (
            r["valid"]
            and r["confidence"] >= 0.70
        )
    )

    unreadable_count = sum(
        1
        for r in results
        if r["status"]
        == "UNREADABLE / LOW CONFIDENCE"
    )

    print()
    print("==========================================")
    print("              OCR SUMMARY")
    print("==========================================")
    print(
        f"Total plate images : {len(results)}"
    )
    print(
        f"Possible valid plates : {valid_count}"
    )
    print(
        f"High-confidence plates : "
        f"{high_confidence_count}"
    )
    print(
        f"Unreadable / low confidence : "
        f"{unreadable_count}"
    )
    print("==========================================")
    print()

    print(
        "✅ OCR testing completed successfully."
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    main()