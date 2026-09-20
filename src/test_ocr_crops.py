import cv2
import easyocr
import os


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

CROPS = [
    "outputs/plates/track_95.jpg",
    "outputs/plates/track_86.jpg",
]


# --------------------------------------------------
# OCR
# --------------------------------------------------

reader = easyocr.Reader(
    ["en"],
    gpu=False
)


def preprocess_variants(image):
    variants = {}

    # 1. Original enlarged
    enlarged = cv2.resize(
        image,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    variants["original_4x"] = enlarged

    # 2. Grayscale
    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    variants["gray"] = gray

    # 3. CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    clahe_img = clahe.apply(gray)
    variants["clahe"] = clahe_img

    # 4. Sharpen
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (3, 3)
    )

    sharpen = cv2.filter2D(
        clahe_img,
        -1,
        kernel
    )

    variants["sharpen"] = sharpen

    # 5. OTSU threshold
    _, otsu = cv2.threshold(
        clahe_img,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    variants["otsu"] = otsu

    # 6. Adaptive threshold
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
# RUN
# --------------------------------------------------

for crop_path in CROPS:

    print("\n" + "=" * 70)
    print("IMAGE:", crop_path)
    print("=" * 70)

    if not os.path.exists(crop_path):
        print("❌ File not found")
        continue

    image = cv2.imread(crop_path)

    if image is None:
        print("❌ Could not read image")
        continue

    variants = preprocess_variants(image)

    for name, img in variants.items():

        results = reader.readtext(
            img,
            detail=1,
            paragraph=False,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

        print(f"\n{name}")

        if not results:
            print("  → No text detected")
            continue

        for bbox, text, confidence in results:
            text = text.upper().replace(" ", "")

            print(
                f"  → {text} "
                f"(confidence={confidence:.3f})"
            )