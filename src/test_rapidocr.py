import cv2
import os
from rapidocr import RapidOCR


# --------------------------------------------------
# TEST PLATES
# --------------------------------------------------

CROPS = [
    ("Track 95", "outputs/plates/track_95.jpg", "EY09VWS"),
    ("Track 86", "outputs/plates/track_86.jpg", "EF10DZT"),
]


# --------------------------------------------------
# RAPIDOCR
# Recognition ONLY
# --------------------------------------------------

print("Loading RapidOCR recognition model...")

ocr = RapidOCR()

print("RapidOCR loaded successfully.")


# --------------------------------------------------
# PREPROCESSING
# --------------------------------------------------

def create_variants(image):

    variants = {}

    # 1. Original 4x
    enlarged = cv2.resize(
        image,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    variants["original_4x"] = enlarged

    # 2. 6x enlargement
    enlarged_6x = cv2.resize(
        image,
        None,
        fx=6,
        fy=6,
        interpolation=cv2.INTER_CUBIC
    )

    variants["original_6x"] = enlarged_6x

    # Use 4x for further processing
    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )

    # 3. Grayscale
    variants["gray"] = gray

    # 4. CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    clahe_img = clahe.apply(gray)

    variants["clahe"] = clahe_img

    # 5. Unsharp masking
    blurred = cv2.GaussianBlur(
        clahe_img,
        (0, 0),
        2
    )

    sharpened = cv2.addWeighted(
        clahe_img,
        1.7,
        blurred,
        -0.7,
        0
    )

    variants["unsharp"] = sharpened

    # 6. OTSU
    _, otsu = cv2.threshold(
        clahe_img,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    variants["otsu"] = otsu

    # 7. Adaptive threshold
    adaptive = cv2.adaptiveThreshold(
        clahe_img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        7
    )

    variants["adaptive"] = adaptive

    return variants


# --------------------------------------------------
# RAPIDOCR RECOGNITION ONLY
# --------------------------------------------------

def run_ocr(image):

    try:

        result = ocr(
            image,
            use_det=False,
            use_cls=False,
            use_rec=True
        )

        # RapidOCR 3.x uses txts and scores
        texts = getattr(result, "txts", None)
        scores = getattr(result, "scores", None)

        if texts is None or scores is None:
            return []

        output = []

        for text, score in zip(texts, scores):

            text = str(text).upper()

            text = "".join(
                c for c in text
                if c.isalnum()
            )

            output.append(
                (text, float(score))
            )

        return output

    except Exception as e:

        print("OCR error:", e)

        return []


# --------------------------------------------------
# TEST
# --------------------------------------------------

for name, path, truth in CROPS:

    print("\n" + "=" * 70)
    print(name)
    print("File        :", path)
    print("Ground truth:", truth)
    print("=" * 70)

    if not os.path.exists(path):

        print("❌ File not found")

        continue

    image = cv2.imread(path)

    if image is None:

        print("❌ Could not read image")

        continue

    variants = create_variants(image)

    for variant_name, variant_image in variants.items():

        results = run_ocr(variant_image)

        print(f"\n{variant_name}")

        if not results:

            print("  → No text recognized")

            continue

        for text, score in results:

            print(
                f"  → {text} "
                f"(confidence={score:.3f})"
            )