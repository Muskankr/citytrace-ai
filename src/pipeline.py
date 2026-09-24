import os
import re
import cv2
from rapidocr import RapidOCR

from typing import Callable, Optional

from ultralytics import YOLO

from src.validator import validate_plate
from src.database_logger import save_detection

from src.ocr_correction import (
    corrected_candidates,
    plate_format_score,
    correct_plate,
    matches_plate_format,
)

from src.best_frame import (
    choose_best_observation,
)

from src.temporal_interpolation import (
    interpolate_plate_observations,
)


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_PATH = "data/videos/sih_traffic.mp4"

VEHICLE_MODEL = "yolo26n.pt"

# Current A/B candidate
PLATE_MODEL = "models/license_plate_github.pt"

CAMERA_CODE = "CAM001"

VEHICLE_CONF = 0.40
PLATE_CONF = 0.20

# Detect plates every N frames
PLATE_INTERVAL = 4

MIN_VEHICLE_WIDTH = 100
MIN_VEHICLE_HEIGHT = 60

OUTPUT_VIDEO = "outputs/videos/github_master_pipeline.mp4"

TEMP_PLATE_DIR = "outputs/pipeline_plates"

# Maximum number of REAL observations used for OCR.
MAX_REAL_OCR = 8

# Maximum number of interpolated observations added for OCR.
MAX_INTERPOLATED_OCR = 4

# ============================================================
# DEMO / RESEARCH MODE
# ============================================================

# True  = faster settings for SIH judge/demo
# False = full research/accuracy pipeline
DEMO_MODE = True

# Fast demo settings
DEMO_PLATE_INTERVAL = 6
DEMO_MAX_REAL_OCR = 4
DEMO_MAX_INTERPOLATED_OCR = 1

# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


# ============================================================
# FOLDERS
# ============================================================

os.makedirs(
    "outputs/videos",
    exist_ok=True
)

os.makedirs(
    "outputs/plates",
    exist_ok=True
)

os.makedirs(
    TEMP_PLATE_DIR,
    exist_ok=True
)


# ============================================================
# IMAGE SHARPNESS
# ============================================================

def calculate_sharpness(image):

    if image is None or image.size == 0:
        return 0.0

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    return float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )


# ============================================================
# PLATE QUALITY
# ============================================================

def calculate_quality_score(
    crop,
    detector_conf
):

    if crop is None or crop.size == 0:
        return 0.0

    height, width = crop.shape[:2]

    if width < 20 or height < 8:
        return 0.0

    sharpness = calculate_sharpness(
        crop
    )

    sharpness_score = min(
        sharpness / 500.0,
        1.0
    )

    area = width * height

    resolution_score = min(
        area / 5000.0,
        1.0
    )

    confidence_score = float(
        detector_conf
    )

    return (
        0.60 * sharpness_score
        + 0.25 * resolution_score
        + 0.15 * confidence_score
    )


# ============================================================
# ENLARGE
# ============================================================

def enlarge_plate(crop):

    return cv2.resize(
        crop,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )


# ============================================================
# NORMALIZE OCR TEXT
# ============================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.upper()

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


# ============================================================
# OCR DIRECTLY ON IMAGE
# ============================================================

# ============================================================
# RAPIDOCR DIRECTLY ON PLATE IMAGE
# ============================================================

def run_ocr(reader, crop):

    if crop is None or crop.size == 0:
        return None

    enlarged = cv2.resize(
        crop,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )

    images = [
        ("original", enlarged),
        ("gray", gray),
    ]

    # --------------------------------------------------------
    # CLAHE
    # --------------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    clahe_img = clahe.apply(gray)

    images.append(
        ("clahe", clahe_img)
    )

    # --------------------------------------------------------
    # UNSHARP
    # --------------------------------------------------------

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

    images.append(
        ("unsharp", sharpened)
    )

    # --------------------------------------------------------
    # OTSU
    # --------------------------------------------------------

    _, otsu = cv2.threshold(
        clahe_img,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    images.append(
        ("otsu", otsu)
    )

    # --------------------------------------------------------
    # ADAPTIVE
    # --------------------------------------------------------

    adaptive = cv2.adaptiveThreshold(
        clahe_img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        7
    )

    images.append(
        ("adaptive", adaptive)
    )

    candidates = []

    # ========================================================
    # RECOGNITION-ONLY RAPIDOCR
    #
    # Plate detector has already located the plate.
    # Therefore we do NOT run RapidOCR text detection again.
    # ========================================================

    for method, image in images:

        try:

            result = reader(
                image,
                use_det=False,
                use_cls=False,
                use_rec=True
            )

            texts = getattr(
                result,
                "txts",
                None
            )

            scores = getattr(
                result,
                "scores",
                None
            )

            if not texts or not scores:
                continue

            for text, confidence in zip(
                texts,
                scores
            ):

                text = normalize_text(
                    text
                )

                if not text:
                    continue

                confidence = float(
                    confidence
                )

                candidate = {
                    "text": text,
                    "confidence": confidence,
                    "method": method,
                }

                candidates.append(
                    candidate
                )

        except Exception as error:

            print(
                f"      RapidOCR error "
                f"({method}): {error}"
            )

    if not candidates:
        return None

    # --------------------------------------------------------
    # Keep all OCR evidence.
    #
    # The downstream temporal-consensus stage can now compare
    # different preprocessing results instead of receiving only
    # the single highest-confidence OCR result.
    # --------------------------------------------------------

    best = max(
        candidates,
        key=lambda item: item["confidence"]
    )

    # Keep all candidates inside the returned result.
    best["candidates"] = candidates

    return best


# ============================================================
# PLATE FORMAT PATTERNS
# ============================================================

PLATE_PATTERNS = [

    # --------------------------------------------------------
    # Standard Indian-style structures
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Additional structures observed in benchmark
    # --------------------------------------------------------

    # GXI50GJ
    # FJI42HY
    # 3 letters + 2 digits + 2 letters
    r"^[A-Z]{3}[0-9]{2}[A-Z]{2}$",

    # EY6INBG
    # AV0BHVF
    # 2 letters + 1 digit + 4 letters
    r"^[A-Z]{2}[0-9][A-Z]{4}$",
]


def possible_plate(text):
    """
    Fast structural check for a possible registration plate.
    """

    if not text:
        return False

    text = normalize_text(text)

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
# OCR CONSENSUS
# ============================================================
# ============================================================
# OCR CONSENSUS
# ============================================================

def _observation_weight(item):
    """
    Calculate evidence weight for one OCR candidate.

    Raw OCR output receives full weight. Generated correction candidates
    receive reduced weight because they are hypotheses derived from the
    same OCR reading, not independent observations.
    """
    confidence = float(item.get("confidence", 0.0))
    quality = float(item.get("quality", 0.0))
    format_score = float(item.get("format_score", 0.0))
    interpolated = bool(item.get("interpolated", False))
    candidate_source = item.get("candidate_source", "raw")

    source_weight = 1.0

    if candidate_source != "raw":
        source_weight *= 0.40

    if interpolated:
        source_weight *= 0.35

    return (
        confidence
        * (0.60 + 0.40 * quality)
        * (0.60 + 0.40 * format_score)
        * source_weight
    )


def _frame_balanced_items(items):
    """
    Prevent the six preprocessing variants from one frame from
    overpowering observations from other frames.

    Each frame keeps approximately the weight of its strongest candidate.
    """
    groups = {}

    for item in items:
        frame = item.get("frame")
        key = frame if frame is not None else id(item)
        groups.setdefault(key, []).append(item)

    balanced = []

    for group in groups.values():
        weights = [_observation_weight(item) for item in group]
        if not weights:
            continue

        strongest = max(weights)
        total = sum(weights)

        if total <= strongest or total <= 0:
            balanced.extend(group)
            continue

        scale = strongest / total

        for item, weight in zip(group, weights):
            copy_item = dict(item)
            copy_item["_balanced_weight"] = weight * scale
            balanced.append(copy_item)

    return balanced


def _character_consensus(items):
    """
    Character-level weighted consensus with plate-structure awareness.

    The consensus uses:
    - frame-balanced OCR evidence
    - raw OCR observations
    - OCR confusion pairs
    - supported letter/digit structures
    - seven-character evidence when sufficiently strong

    It does NOT blindly force a single hard-coded plate format.
    """

    valid_items = []

    for item in items:
        text = normalize_text(item.get("text", ""))

        if len(text) < 6 or len(text) > 10:
            continue

        copy_item = dict(item)
        copy_item["text"] = text
        copy_item["_raw_weight"] = _observation_weight(copy_item)

        valid_items.append(copy_item)

    if not valid_items:
        return None

    # --------------------------------------------------------
    # Balance evidence from the same video frame.
    # --------------------------------------------------------

    valid_items = _frame_balanced_items(valid_items)

    # --------------------------------------------------------
    # Group observations by plate length.
    # --------------------------------------------------------

    length_groups = {}

    for item in valid_items:

        text = item["text"]

        weight = float(
            item.get(
                "_balanced_weight",
                item.get("_raw_weight", 0.0)
            )
        )

        length_groups.setdefault(
            len(text),
            []
        ).append(
            (text, weight, item)
        )

    if not length_groups:
        return None

    length_scores = {
        length: sum(
            weight
            for _, weight, _ in group
        )
        for length, group in length_groups.items()
    }

    # --------------------------------------------------------
    # Select the dominant plate length.
    # --------------------------------------------------------

    best_length = max(
        length_scores,
        key=length_scores.get
    )

    # Seven-character plates are important for this prototype,
    # but we only prefer them when they have meaningful support.
    if 7 in length_scores:

        strongest_score = length_scores[best_length]
        seven_score = length_scores[7]

        if seven_score >= strongest_score * 0.75:
            best_length = 7

    candidates = length_groups[best_length]

    # --------------------------------------------------------
    # Supported letter/digit structures.
    # --------------------------------------------------------

    structures = [
        "LLDDLLL",
        "LLDDLL",
        "LLDDL",
        "LLDDLLDDDD",
        "LLDDLLLDDDD",
        "LLDLLDDDD",
        "LLDLLLDDDD",
        "LLLDDLL",
        "LLDLLLL",
    ]

    structures = [
        structure
        for structure in structures
        if len(structure) == best_length
    ]

    # --------------------------------------------------------
    # OCR confusion pairs.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Find the best structure using the actual OCR evidence.
    # --------------------------------------------------------

    def structure_evidence(structure):

        score = 0.0

        for position in range(best_length):

            position_scores = {}

            for text, weight, _ in candidates:

                if position >= len(text):
                    continue

                char = text[position]

                position_scores[char] = (
                    position_scores.get(char, 0.0)
                    + weight
                )

            if not position_scores:
                continue

            letter_score = sum(
                value
                for char, value in position_scores.items()
                if char.isalpha()
            )

            digit_score = sum(
                value
                for char, value in position_scores.items()
                if char.isdigit()
            )

            expected = structure[position]

            if expected == "L":
                score += letter_score

            elif expected == "D":
                score += digit_score

        return score

    if structures:

        best_structure = max(
            structures,
            key=structure_evidence
        )

    else:
        best_structure = None

    # --------------------------------------------------------
    # Character consensus using the selected structure.
    # --------------------------------------------------------

    result = []

    for position in range(best_length):

        char_scores = {}

        for text, weight, _ in candidates:

            if position >= len(text):
                continue

            char = text[position]

            expected = (
                best_structure[position]
                if best_structure
                else None
            )

            # ------------------------------------------------
            # Direct evidence.
            # ------------------------------------------------

            direct_weight = weight

            char_scores[char] = (
                char_scores.get(char, 0.0)
                + direct_weight
            )

            # ------------------------------------------------
            # OCR confusion evidence.
            #
            # If the structure says this position should be a
            # digit and OCR produced O/I/S/etc., also give the
            # corresponding digit some evidence.
            # ------------------------------------------------

            if expected == "D":

                corrected = digit_confusions.get(char)

                if corrected:

                    char_scores[corrected] = (
                        char_scores.get(corrected, 0.0)
                        + weight * 0.85
                    )

            elif expected == "L":

                corrected = letter_confusions.get(char)

                if corrected:

                    char_scores[corrected] = (
                        char_scores.get(corrected, 0.0)
                        + weight * 0.85
                    )

        # ----------------------------------------------------
        # Remove characters that violate the expected class.
        # ----------------------------------------------------

        if best_structure:

            expected = best_structure[position]

            if expected == "D":

                char_scores = {
                    char: score
                    for char, score in char_scores.items()
                    if char.isdigit()
                }

            elif expected == "L":

                char_scores = {
                    char: score
                    for char, score in char_scores.items()
                    if char.isalpha()
                }

        if char_scores:

            best_char = max(
                char_scores,
                key=char_scores.get
            )

            result.append(best_char)

    if not result:
        return None

    return "".join(result)


def choose_consensus(observations):
    if not observations:
        return None

    cleaned = []

    for item in observations:
        text = normalize_text(item.get("text", ""))

        if not text:
            continue

        item_copy = dict(item)
        item_copy["text"] = text
        item_copy["format_score"] = plate_format_score(text)
        item_copy["valid_shape"] = possible_plate(text)

        cleaned.append(item_copy)

    if not cleaned:
        return None

    consensus_text = _character_consensus(cleaned)

    if not consensus_text:
        return None

    # DO NOT blindly run correct_plate() on the final consensus.
    # The candidate-generation stage already creates correction hypotheses.
    # Applying position correction here can turn a correct B into 8, etc.
    consensus_format = plate_format_score(consensus_text)
    consensus_valid = possible_plate(consensus_text)

    # Find observations supporting the final consensus.
    supporting_items = []

    for item in cleaned:
        text = item["text"]

        if text == consensus_text:
            similarity = 1.0

        elif len(text) == len(consensus_text):
            matching_chars = sum(
                1
                for a, b in zip(text, consensus_text)
                if a == b
            )
            similarity = (
                matching_chars / len(consensus_text)
            )

        else:
            similarity = 0.0

        if similarity >= 0.70:
            supporting_items.append(
                (item, similarity)
            )

    total_weight = 0.0
    confidence_weight = 0.0
    quality_weight = 0.0

    real_frames = set()
    interpolated_frames = set()

    for item, similarity in supporting_items:
        weight = (
            _observation_weight(item)
            * similarity
        )

        total_weight += weight

        confidence_weight += (
            float(item.get("confidence", 0.0))
            * weight
        )

        quality_weight += (
            float(item.get("quality", 0.0))
            * weight
        )

        frame = item.get("frame")

        if item.get("interpolated", False):
            if frame is not None:
                interpolated_frames.add(frame)
        else:
            if frame is not None:
                real_frames.add(frame)

    if total_weight > 0:
        weighted_confidence = (
            confidence_weight / total_weight
        )

        weighted_quality = (
            quality_weight / total_weight
        )
    else:
        weighted_confidence = 0.0
        weighted_quality = 0.0

    evidence_score = min(
        total_weight / 3.0,
        1.0
    )

    # A repeated plate supported by several distinct frames receives more
    # evidence than one appearing in only a single frame.
    frame_evidence = min(
        len(real_frames) / 4.0,
        1.0
    )

    score = (
        0.30 * weighted_confidence
        + 0.20 * weighted_quality
        + 0.25 * consensus_format
        + 0.15 * evidence_score
        + 0.10 * frame_evidence
    )

    return {
        "text": consensus_text,
        "confidence": weighted_confidence,
        "quality": weighted_quality,
        "count": len(real_frames) + len(interpolated_frames),
        "real_count": len(real_frames),
        "interpolated_count": len(interpolated_frames),
        "valid_shape": consensus_valid,
        "format_score": consensus_format,
        "score": score,
        "supporting_items": [
            item
            for item, _ in supporting_items
        ],
    }


# ============================================================
# EXTRACT GLOBAL PLATE CROP
# ============================================================

def extract_global_plate_crop(
    frame,
    bbox
):

    if frame is None:
        return None

    height, width = frame.shape[:2]

    x1, y1, x2, y2 = map(
        int,
        bbox
    )

    x1 = max(
        0,
        min(width - 1, x1)
    )

    y1 = max(
        0,
        min(height - 1, y1)
    )

    x2 = max(
        0,
        min(width, x2)
    )

    y2 = max(
        0,
        min(height, y2)
    )

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[
        y1:y2,
        x1:x2
    ].copy()

    if crop.size == 0:
        return None

    if crop.shape[1] < 25:
        return None

    if crop.shape[0] < 8:
        return None

    return crop


# ============================================================
# BUILD INTERPOLATED OBSERVATIONS
# ============================================================

def build_interpolated_observations(
    video_path,
    observations,
):

    if len(observations) < 2:
        return observations.copy()

    # --------------------------------------------------------
    # Temporal interpolation uses GLOBAL plate coordinates.
    # --------------------------------------------------------

    temporal_input = []

    for obs in observations:

        if "bbox" not in obs:
            continue

        temporal_input.append({

            "frame": int(
                obs["frame"]
            ),

            "bbox": [
                float(x)
                for x in obs["bbox"]
            ],

            "confidence": float(
                obs.get(
                    "plate_confidence",
                    0.0
                )
            ),

            "quality": float(
                obs.get(
                    "quality",
                    0.0
                )
            ),

            "interpolated": False,
        })

    if len(temporal_input) < 2:
        return observations.copy()

    interpolated = (
        interpolate_plate_observations(
            temporal_input
        )
    )

    real_frames = {
        int(obs["frame"])
        for obs in observations
    }

    generated = []

    # --------------------------------------------------------
    # Reopen video only for interpolated frames.
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():
        return observations.copy()

    try:

        for item in interpolated:

            if not item.get(
                "interpolated",
                False
            ):
                continue

            frame_number = int(
                item["frame"]
            )

            if frame_number in real_frames:
                continue

            cap.set(
                cv2.CAP_PROP_POS_FRAMES,
                max(0, frame_number - 1)
            )

            success, frame = cap.read()

            if not success:
                continue

            crop = extract_global_plate_crop(
                frame,
                item["bbox"]
            )

            if crop is None:
                continue

            sharpness = calculate_sharpness(
                crop
            )

            quality = calculate_quality_score(
                crop,
                0.0
            )

            generated.append({

                "crop": crop,

                "quality": quality,

                "sharpness": sharpness,

                "plate_confidence": 0.0,

                "frame": frame_number,

                "bbox": item["bbox"],

                "interpolated": True,
            })

    finally:

        cap.release()

    return (
        observations
        + generated
    )


def select_temporally_diverse(observations, max_count, min_frame_gap=12):
    """
    Select strong observations while avoiding eight nearly identical
    frames from one moment. Temporal diversity gives consensus genuinely
    different views of the same tracked vehicle.
    """
    if len(observations) <= max_count:
        return list(observations)

    ranked = sorted(
        observations,
        key=lambda x: (
            x.get("quality", 0.0),
            x.get("sharpness", 0.0),
        ),
        reverse=True,
    )

    selected = []

    for observation in ranked:
        frame = int(observation.get("frame", 0))

        if all(
            abs(
                frame - int(existing.get("frame", 0))
            ) >= min_frame_gap
            for existing in selected
        ):
            selected.append(observation)

        if len(selected) >= max_count:
            break

    # If the video is short and the spacing rule left gaps, fill the
    # remaining slots with the strongest unused observations.
    if len(selected) < max_count:
        selected_frames = {
            int(x.get("frame", 0))
            for x in selected
        }

        for observation in ranked:
            frame = int(observation.get("frame", 0))

            if frame in selected_frames:
                continue

            selected.append(observation)
            selected_frames.add(frame)

            if len(selected) >= max_count:
                break

    return selected


# ============================================================
# MAIN PIPELINE
# ============================================================

def main(
    video_path=VIDEO_PATH,
    camera_code=CAMERA_CODE,
    progress_callback: Optional[
        Callable[[int, int], None]
    ] = None
):

    print()
    print("=" * 70)
    print("        SIH26127 MASTER AI ANPR PIPELINE")
    print("=" * 70)
    print()

    # ========================================================
    # LOAD MODELS
    # ========================================================

    print(
        "Loading vehicle detection model..."
    )

    vehicle_model = YOLO(
        VEHICLE_MODEL
    )

    print(
        "Loading license plate model..."
    )

    plate_model = YOLO(
        PLATE_MODEL
    )

    print(
    "Loading RapidOCR engine..."
)

    reader = RapidOCR()

    print(
        "✅ All AI models loaded."
    )

    print()

    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():

        print(
            f"❌ Could not open video: "
            f"{video_path}"
        )

        return

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 30

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print(
        "VIDEO INFORMATION"
    )

    print(
        "-" * 70
    )

    print(
        f"Camera       : {camera_code}"
    )

    print(
        f"Resolution   : "
        f"{width} x {height}"
    )

    print(
        f"FPS          : {fps:.2f}"
    )

    print(
        f"Total frames : {total_frames}"
    )

    print()

    # ========================================================
    # OUTPUT VIDEO
    # ========================================================

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    out = cv2.VideoWriter(
        OUTPUT_VIDEO,
        fourcc,
        fps,
        (width, height)
    )

    if not out.isOpened():

        cap.release()

        print(
            "❌ Could not create output video."
        )

        return

    # ========================================================
    # TRACK DATA
    # ========================================================

    track_data = {}

    frame_number = 0

    # ========================================================
    # PROGRESS
    # ========================================================

    def report_progress(
        current_frame
    ):

        if (
            progress_callback is None
            or total_frames <= 0
        ):
            return

        ratio = (
            current_frame
            / total_frames
        )

        progress = 10 + int(
            ratio * 85
        )

        progress = max(
            10,
            min(
                95,
                progress
            )
        )

        try:

            progress_callback(
                current_frame,
                total_frames
            )

        except Exception as error:

            print(
                f"Progress callback warning: "
                f"{error}"
            )

        if (
            current_frame % 50 == 0
            or current_frame == total_frames
        ):

            print(
                f"Processing: "
                f"{current_frame}/"
                f"{total_frames} "
                f"({ratio * 100:.1f}%)"
            )

    if progress_callback:

        try:

            progress_callback(
                0,
                total_frames
            )

        except Exception:
            pass

    # ========================================================
    # VIDEO LOOP
    # ========================================================

    try:

        while True:

            success, frame = cap.read()

            if not success:
                break

            frame_number += 1

            if (
                frame_number % 10 == 0
                or frame_number == total_frames
            ):

                report_progress(
                    frame_number
                )

            clean_frame = frame.copy()

            # ------------------------------------------------
            # VEHICLE TRACKING
            # ------------------------------------------------

            results = vehicle_model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                conf=VEHICLE_CONF,
                classes=list(
                    VEHICLE_CLASSES.keys()
                ),
                verbose=False
            )

            if len(results) == 0:

                out.write(
                    frame
                )

                continue

            result = results[0]

            if (
                result.boxes is None
                or result.boxes.id is None
            ):

                out.write(
                    frame
                )

                continue

            boxes = (
                result.boxes.xyxy
                .cpu()
                .numpy()
            )

            track_ids = (
                result.boxes.id
                .cpu()
                .numpy()
                .astype(int)
            )

            classes = (
                result.boxes.cls
                .cpu()
                .numpy()
                .astype(int)
            )

            vehicle_confidences = (
                result.boxes.conf
                .cpu()
                .numpy()
            )

            # =================================================
            # VEHICLES
            # =================================================

            for (
                box,
                track_id,
                class_id,
                vehicle_conf
            ) in zip(
                boxes,
                track_ids,
                classes,
                vehicle_confidences
            ):

                if class_id not in VEHICLE_CLASSES:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    box
                )

                x1 = max(
                    0,
                    x1
                )

                y1 = max(
                    0,
                    y1
                )

                x2 = min(
                    width,
                    x2
                )

                y2 = min(
                    height,
                    y2
                )

                vehicle_width = (
                    x2 - x1
                )

                vehicle_height = (
                    y2 - y1
                )

                if (
                    vehicle_width <= 0
                    or vehicle_height <= 0
                ):
                    continue

                vehicle_name = (
                    VEHICLE_CLASSES[
                        class_id
                    ]
                )

                # ------------------------------------------------
                # DRAW VEHICLE
                # ------------------------------------------------

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    2
                )

                cv2.putText(
                    frame,
                    (
                        f"{vehicle_name} "
                        f"ID:{track_id}"
                    ),
                    (
                        x1,
                        max(
                            25,
                            y1 - 8
                        )
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 0, 0),
                    2
                )

                # PLATE INTERVAL
# ------------------------------------------------

                current_plate_interval = (
                    DEMO_PLATE_INTERVAL
                    if DEMO_MODE
                    else PLATE_INTERVAL
                )

                if (
                    frame_number
                    % current_plate_interval != 0
                ):
                    continue

                if (
                    vehicle_width
                    < MIN_VEHICLE_WIDTH
                    or vehicle_height
                    < MIN_VEHICLE_HEIGHT
                ):
                    continue

                vehicle_crop = clean_frame[
                    y1:y2,
                    x1:x2
                ]

                if vehicle_crop.size == 0:
                    continue

                # ------------------------------------------------
                # PLATE DETECTOR
                # ------------------------------------------------

                plate_results = (
                    plate_model.predict(
                        vehicle_crop,
                        conf=PLATE_CONF,
                        imgsz=640,
                        verbose=False
                    )
                )

                if len(plate_results) == 0:
                    continue

                plate_result = (
                    plate_results[0]
                )

                if plate_result.boxes is None:
                    continue

                # ------------------------------------------------
                # PLATE CANDIDATES
                # ------------------------------------------------

                for (
                    plate_box,
                    plate_conf
                ) in zip(
                    plate_result.boxes.xyxy.cpu().numpy(),
                    plate_result.boxes.conf.cpu().numpy()
                ):

                    px1, py1, px2, py2 = map(
                        int,
                        plate_box
                    )

                    vh, vw = (
                        vehicle_crop.shape[:2]
                    )

                    px1 = max(
                        0,
                        px1
                    )

                    py1 = max(
                        0,
                        py1
                    )

                    px2 = min(
                        vw,
                        px2
                    )

                    py2 = min(
                        vh,
                        py2
                    )

                    plate_width = (
                        px2 - px1
                    )

                    plate_height = (
                        py2 - py1
                    )

                    if (
                        plate_width < 25
                        or plate_height < 8
                    ):
                        continue

                    plate_crop = (
                        vehicle_crop[
                            py1:py2,
                            px1:px2
                        ].copy()
                    )

                    if plate_crop.size == 0:
                        continue

                    # ------------------------------------------------
                    # GLOBAL PLATE BBOX
                    #
                    # Needed for temporal interpolation.
                    # ------------------------------------------------

                    global_bbox = [
                        x1 + px1,
                        y1 + py1,
                        x1 + px2,
                        y1 + py2,
                    ]

                    # ------------------------------------------------
                    # QUALITY
                    # ------------------------------------------------

                    sharpness = (
                        calculate_sharpness(
                            plate_crop
                        )
                    )

                    quality = (
                        calculate_quality_score(
                            plate_crop,
                            float(
                                plate_conf
                            )
                        )
                    )

                    # ------------------------------------------------
                    # INITIALIZE TRACK
                    # ------------------------------------------------

                    if track_id not in track_data:

                        track_data[
                            track_id
                        ] = {

                            "observations": [],

                            "vehicle_type": (
                                vehicle_name
                            ),

                            "vehicle_confidence": (
                                float(
                                    vehicle_conf
                                )
                            ),

                            "plate_confidence": (
                                float(
                                    plate_conf
                                )
                            ),

                            "frame": (
                                frame_number
                            ),
                        }

                    data = track_data[
                        track_id
                    ]

                    # ------------------------------------------------
                    # SAVE OBSERVATION
                    # ------------------------------------------------

                    data[
                        "observations"
                    ].append({

                        "crop": (
                            plate_crop.copy()
                        ),

                        "quality": (
                            quality
                        ),

                        "sharpness": (
                            sharpness
                        ),

                        "plate_confidence": (
                            float(
                                plate_conf
                            )
                        ),

                        "frame": (
                            frame_number
                        ),

                        "bbox": (
                            global_bbox
                        ),

                        "interpolated": False,
                    })

                    # ------------------------------------------------
                    # DRAW PLATE
                    # ------------------------------------------------

                    gx1 = x1 + px1
                    gy1 = y1 + py1
                    gx2 = x1 + px2
                    gy2 = y1 + py2

                    cv2.rectangle(
                        frame,
                        (gx1, gy1),
                        (gx2, gy2),
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        (
                            f"PLATE "
                            f"{plate_conf:.2f}"
                        ),
                        (
                            gx1,
                            max(
                                20,
                                gy1 - 5
                            )
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        (0, 255, 0),
                        1
                    )

            # ------------------------------------------------
            # WRITE FRAME
            # ------------------------------------------------

            out.write(
                frame
            )

    finally:

        cap.release()
        out.release()

    # ========================================================
    # VIDEO COMPLETE
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "VIDEO PROCESSING COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Tracks with plate candidates: "
        f"{len(track_data)}"
    )

    print(
        f"Output video: "
        f"{OUTPUT_VIDEO}"
    )

    print()

    # ========================================================
    # OCR
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "TEMPORAL OCR + CONSENSUS + VALIDATION"
    )

    print(
        "=" * 70
    )

    print()

    successful_detections = 0

    total_tracks = len(
        track_data
    )

    processed_tracks = 0

    # ========================================================
    # PROCESS EACH TRACK
    # ========================================================

    for track_id, data in track_data.items():

        processed_tracks += 1

        real_observations = data[
            "observations"
        ]

        if not real_observations:
            continue

        print(
            f"Track {track_id} "
            f"({len(real_observations)} "
            f"real plate observations)"
        )

        # ----------------------------------------------------
        # TEMPORAL INTERPOLATION
        # ----------------------------------------------------

        all_observations = (
            build_interpolated_observations(
                video_path,
                real_observations
            )
        )

        interpolated_count = sum(
            1
            for x in all_observations
            if x.get(
                "interpolated",
                False
            )
        )

        if interpolated_count:

            print(
                f"    Temporal interpolation: "
                f"+{interpolated_count} "
                f"estimated observations"
            )

        # ----------------------------------------------------
        # SELECT STRONGEST REAL OBSERVATIONS
        # ----------------------------------------------------

        real_for_ocr = [
            x
            for x in all_observations
            if not x.get(
                "interpolated",
                False
            )
        ]

        real_for_ocr = select_temporally_diverse(
            real_for_ocr,
            (
                DEMO_MAX_REAL_OCR
                if DEMO_MODE
                else MAX_REAL_OCR
        ),
            min_frame_gap=12,
        )

        # ----------------------------------------------------
        # SELECT A FEW INTERPOLATED OBSERVATIONS
        #
        # These can recover a sharper frame between
        # detector observations.
        # ----------------------------------------------------

        interpolated_for_ocr = [
            x
            for x in all_observations
            if x.get(
                "interpolated",
                False
            )
        ]

        interpolated_for_ocr = select_temporally_diverse(
            interpolated_for_ocr,
            (
                DEMO_MAX_INTERPOLATED_OCR
                if DEMO_MODE
                else MAX_INTERPOLATED_OCR
            ),
            min_frame_gap=12,
        )

        selected_observations = (
            real_for_ocr
            + interpolated_for_ocr
        )

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        ocr_observations = []

        for observation in selected_observations:

            result = run_ocr(
                reader,
                observation["crop"]
            )

            if result is None:
                continue

            # ------------------------------------------------
            # Get ALL OCR candidates from all preprocessing
            # methods.
            # ------------------------------------------------

            raw_candidates = result.get(
                "candidates",
                []
            )

            # Fallback if candidates are unavailable.
            if not raw_candidates:

                raw_candidates = [
                    {
                        "text": result.get(
                            "text",
                            ""
                        ),
                        "confidence": result.get(
                            "confidence",
                            0.0
                        ),
                        "method": result.get(
                            "method",
                            "unknown"
                        ),
                    }
                ]

            # ------------------------------------------------
            # Calculate crop resolution.
            # ------------------------------------------------

            crop_height, crop_width = (
                observation["crop"].shape[:2]
            )

            resolution = (
                crop_width
                * crop_height
            )

            # ------------------------------------------------
            # Process every OCR candidate.
            # ------------------------------------------------

            for raw_candidate in raw_candidates:

                raw_text = normalize_text(
                    raw_candidate.get(
                        "text",
                        ""
                    )
                )

                if not raw_text:
                    continue

                confidence = float(
                    raw_candidate.get(
                        "confidence",
                        0.0
                    )
                )

                method = raw_candidate.get(
                    "method",
                    "unknown"
                )

                # ------------------------------------------------
                # Generate original + corrected candidates.
                # ------------------------------------------------

                candidate_texts = set(
                    corrected_candidates(
                        raw_text
                    )
                )

                position_corrected = (
                    correct_plate(
                        raw_text
                    )
                )

                if position_corrected:
                    candidate_texts.add(
                        position_corrected
                    )

                # ------------------------------------------------
                # Add every candidate to OCR observations.
                # ------------------------------------------------

                for text in candidate_texts:

                    text = normalize_text(
                        text
                    )

                    if not text:
                        continue

                    format_score = (
                        plate_format_score(
                            text
                        )
                    )

                    valid_shape = (
                        possible_plate(
                            text
                        )
                    )

                    candidate_item = {

                        "text": text,

                        # Keep track of whether this text came directly
                        # from OCR or was generated as a correction candidate.
                        # Generated candidates are supporting evidence, not
                        # independent OCR observations.
                        "candidate_source": (
                            "raw"
                            if text == raw_text
                            else "generated"
                        ),

                        "confidence": (
                            confidence
                        ),

                        "quality": (
                            observation[
                                "quality"
                            ]
                        ),

                        "sharpness": (
                            observation[
                                "sharpness"
                            ]
                        ),

                        "frame": (
                            observation[
                                "frame"
                            ]
                        ),

                        "detector_confidence": (
                            observation[
                                "plate_confidence"
                            ]
                        ),

                        "resolution": (
                            resolution
                        ),

                        "format_score": (
                            format_score
                        ),

                        "valid": (
                            valid_shape
                        ),

                        "method": method,

                        "interpolated": (
                            observation.get(
                                "interpolated",
                                False
                            )
                        ),
                    }

                    ocr_observations.append(
                        candidate_item
                    )

                    print(
                        f"    Frame "
                        f"{observation['frame']}: "
                        f"{text} "
                        f"(OCR={confidence:.2f}, "
                        f"method={method}, "
                        f"format={format_score:.2f}"
                        f"{', interp' if observation.get('interpolated', False) else ''})"
                    )

        # ----------------------------------------------------
        # OCR PROGRESS
        # ----------------------------------------------------

        if (
            progress_callback
            and total_tracks > 0
        ):

            try:

                progress_callback(
                    total_frames,
                    total_frames
                )

            except Exception:
                pass

        if not ocr_observations:

            print(
                "    ⚠ No OCR result."
            )

            print()

            continue

        # ----------------------------------------------------
        # BEST OBSERVATION SCORING
        # ----------------------------------------------------

        best_observation = (
            choose_best_observation(
                ocr_observations
            )
        )

        if best_observation:

            print(
                f"    Best frame: "
                f"{best_observation['frame']} "
                f"score="
                f"{best_observation['overall_score']:.3f}"
            )

        # ----------------------------------------------------
        # CONSENSUS
        # ----------------------------------------------------

        consensus = choose_consensus(
            ocr_observations
        )

        if consensus is None:

            print(
                "    ⚠ No consensus."
            )

            print()

            continue

        plate_number = (
            consensus["text"]
        )

        print(
            f"    CONSENSUS: "
            f"{plate_number}"
        )

        print(
            f"    OCR confidence: "
            f"{consensus['confidence']:.2f}"
        )

        print(
            f"    Format score: "
            f"{consensus['format_score']:.2f}"
        )

        print(
            f"    Repeated observations: "
            f"{consensus['count']}"
        )

        # ----------------------------------------------------
        # FINAL VALIDATION
        # ----------------------------------------------------

        validation = validate_plate(
            plate_number,
            consensus[
                "confidence"
            ]
        )

        print(
            f"    Validation: "
            f"{validation['status']}"
        )

        # ----------------------------------------------------
        # SAVE VALID PLATE
        # ----------------------------------------------------

        if validation["valid"]:

            # Use the strongest observation
            # corresponding to the final plate.
            matching = [
                x
                for x in ocr_observations
                if x["text"]
                == plate_number
            ]

            if matching:

                best_final = (
                    choose_best_observation(
                        matching
                    )
                )

            else:

                best_final = (
                    best_observation
                )

            if best_final is None:

                best_final = {
                    "frame": data[
                        "frame"
                    ],
                    "detector_confidence": (
                        data[
                            "plate_confidence"
                        ]
                    ),
                }

            saved = save_detection(

                camera_code=(
                    camera_code
                ),

                track_id=(
                    track_id
                ),

                vehicle_type=(
                    data[
                        "vehicle_type"
                    ]
                ),

                plate_number=(
                    validation[
                        "plate_number"
                    ]
                ),

                ocr_confidence=(
                    consensus[
                        "confidence"
                    ]
                ),

                plate_valid=True,

                plate_status=(
                    validation[
                        "status"
                    ]
                ),

                frame_number=(
                    best_final[
                        "frame"
                    ]
                ),

                vehicle_confidence=(
                    data[
                        "vehicle_confidence"
                    ]
                ),

                plate_detection_confidence=(
                    data[
                        "plate_confidence"
                    ]
                ),
            )

            if saved:

                successful_detections += 1

                print(
                    "    ✅ SAVED TO DATABASE"
                )

        else:

            print(
                "    ⚠ Not saved as valid plate."
            )

        print()

    # ========================================================
    # FINAL PROGRESS
    # ========================================================

    if progress_callback:

        try:

            progress_callback(
                total_frames,
                total_frames
            )

        except Exception:
            pass

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print(
        "=" * 70
    )

    print(
        "          MASTER PIPELINE COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Plate candidates : "
        f"{len(track_data)}"
    )

    print(
        f"Valid DB records : "
        f"{successful_detections}"
    )

    print(
        f"Video output     : "
        f"{OUTPUT_VIDEO}"
    )

    print()

    print(
        "Next stage:"
    )

    print(
        "Trajectory → Analytics → Alerts → Dashboard"
    )

    print(
        "=" * 70
    )


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    main()