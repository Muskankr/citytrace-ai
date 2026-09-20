from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from database.models import VehicleDetection
from api.schemas import DetectionResponse


router = APIRouter(
    prefix="/detections",
    tags=["Detections"]
)


def normalize_track_id(track_id):
    """
    Convert database track IDs into a normal Python integer.

    Older records may contain track IDs stored as bytes,
    while newer records should contain integers.
    """
    if track_id is None:
        return None

    if isinstance(track_id, bytes):
        return int.from_bytes(track_id, byteorder="little")

    return int(track_id)


def detection_to_response(detection):
    """
    Convert a VehicleDetection database object
    into a DetectionResponse safely.
    """
    return DetectionResponse(
        id=detection.id,

        track_id=normalize_track_id(detection.track_id),

        vehicle_type=detection.vehicle_type,
        plate_number=detection.plate_number,
        ocr_confidence=detection.ocr_confidence,
        plate_valid=detection.plate_valid,
        plate_status=detection.plate_status,

        # Return CAM001, CAM002, etc.
        # instead of the internal database ID.
        camera_id=detection.camera.camera_id,

        latitude=detection.latitude,
        longitude=detection.longitude,
        direction=detection.direction,
        timestamp=detection.timestamp,
        frame_number=detection.frame_number,
        vehicle_confidence=detection.vehicle_confidence,
        plate_detection_confidence=detection.plate_detection_confidence,
    )


# ============================================================
# GET ALL DETECTIONS
# ============================================================

@router.get("/", response_model=list[DetectionResponse])
def get_detections(db: Session = Depends(get_db)):

    detections = (
        db.query(VehicleDetection)
        .options(joinedload(VehicleDetection.camera))
        .order_by(VehicleDetection.timestamp.desc())
        .all()
    )

    return [
        detection_to_response(detection)
        for detection in detections
    ]


# ============================================================
# GET DETECTIONS BY PLATE
# ============================================================

@router.get(
    "/plate/{plate_number}",
    response_model=list[DetectionResponse]
)
def get_detections_by_plate(
    plate_number: str,
    db: Session = Depends(get_db)
):

    detections = (
        db.query(VehicleDetection)
        .options(joinedload(VehicleDetection.camera))
        .filter(
            VehicleDetection.plate_number == plate_number
        )
        .order_by(VehicleDetection.timestamp.asc())
        .all()
    )

    return [
        detection_to_response(detection)
        for detection in detections
    ]


# ============================================================
# GET DETECTIONS BY CAMERA
# ============================================================

@router.get(
    "/camera/{camera_id}",
    response_model=list[DetectionResponse]
)
def get_detections_by_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):

    detections = (
        db.query(VehicleDetection)
        .join(VehicleDetection.camera)
        .options(joinedload(VehicleDetection.camera))
        .filter(
            VehicleDetection.camera.has(
                camera_id=camera_id
            )
        )
        .order_by(VehicleDetection.timestamp.desc())
        .all()
    )

    return [
        detection_to_response(detection)
        for detection in detections
    ]