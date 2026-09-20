from datetime import datetime

from database.database import SessionLocal
from database.models import VehicleDetection, Camera


def get_camera(db, camera_code):
    """
    Find camera using CAM001, CAM002, etc.
    """

    camera = (
        db.query(Camera)
        .filter(Camera.camera_id == camera_code)
        .first()
    )

    return camera


def save_detection(
    camera_code,
    track_id,
    vehicle_type,
    plate_number=None,
    ocr_confidence=0.0,
    plate_valid=False,
    plate_status="UNREADABLE",
    latitude=None,
    longitude=None,
    direction=None,
    frame_number=None,
    vehicle_confidence=0.0,
    plate_detection_confidence=0.0,
):
    """
    Save one vehicle detection into the database.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Find camera
        # ----------------------------------------------------

        camera = get_camera(db, camera_code)

        if camera is None:
            print(f"❌ Camera not found: {camera_code}")
            return False

        # ----------------------------------------------------
        # Normalize Track ID
        # ----------------------------------------------------
        # YOLO / NumPy may sometimes return a NumPy integer.
        # Convert it to a normal Python int before saving.
        # This prevents bytes-like Track IDs from entering
        # the database.
        # ----------------------------------------------------

        if track_id is not None:
            track_id = int(track_id)

        # ----------------------------------------------------
        # Create detection record
        # ----------------------------------------------------

        detection = VehicleDetection(

            track_id=track_id,

            vehicle_type=vehicle_type,

            plate_number=plate_number,

            ocr_confidence=ocr_confidence,

            plate_valid=plate_valid,

            plate_status=plate_status,

            camera_id=camera.id,

            latitude=(
                latitude
                if latitude is not None
                else camera.latitude
            ),

            longitude=(
                longitude
                if longitude is not None
                else camera.longitude
            ),

            direction=(
                direction
                if direction is not None
                else camera.direction
            ),

            timestamp=datetime.utcnow(),

            frame_number=frame_number,

            vehicle_confidence=vehicle_confidence,

            plate_detection_confidence=(
                plate_detection_confidence
            ),
        )

        db.add(detection)

        db.commit()

        db.refresh(detection)

        print(
            f"✅ Detection saved | "
            f"Camera: {camera_code} | "
            f"Track: {track_id} | "
            f"Plate: {plate_number or 'UNKNOWN'}"
        )

        return True

    except Exception as e:

        db.rollback()

        print(
            f"❌ Database error: {e}"
        )

        return False

    finally:

        db.close()


# ============================================================
# TEST DATABASE LOGGER
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("DATABASE LOGGER TEST")
    print("=" * 60)

    result = save_detection(
        camera_code="CAM001",

        track_id=101,

        vehicle_type="car",

        plate_number="HR26AB1234",

        ocr_confidence=0.92,

        plate_valid=True,

        plate_status="VALID",

        frame_number=120,

        vehicle_confidence=0.91,

        plate_detection_confidence=0.88,
    )

    print()

    if result:
        print(
            "🎉 Database logger test successful!"
        )
    else:
        print(
            "❌ Database logger test failed."
        )