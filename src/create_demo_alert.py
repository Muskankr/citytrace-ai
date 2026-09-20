from database.database import SessionLocal
from database.models import VehicleDetection, Camera


DEMO_PLATE = "HR26XY9999"
DEMO_CAMERA = "CAM002"


def create_demo_detection():

    db = SessionLocal()

    try:

        camera = (
            db.query(Camera)
            .filter(Camera.camera_id == DEMO_CAMERA)
            .first()
        )

        if camera is None:
            print(f"❌ Camera {DEMO_CAMERA} not found.")
            return

        existing = (
            db.query(VehicleDetection)
            .filter(
                VehicleDetection.plate_number == DEMO_PLATE,
                VehicleDetection.camera_id == camera.id,
            )
            .first()
        )

        if existing:
            print("⚠️ Demo blacklisted detection already exists.")
            return

        detection = VehicleDetection(
            track_id=999,
            vehicle_type="car",
            plate_number=DEMO_PLATE,
            ocr_confidence=0.95,
            plate_valid=True,
            plate_status="VALID",
            camera_id=camera.id,
            latitude=camera.latitude,
            longitude=camera.longitude,
            direction=camera.direction,
            vehicle_confidence=0.94,
            plate_detection_confidence=0.96,
        )

        db.add(detection)
        db.commit()

        print("=" * 60)
        print("DEMO DETECTION CREATED")
        print("=" * 60)
        print(f"Plate      : {DEMO_PLATE}")
        print(f"Camera     : {DEMO_CAMERA}")
        print("Vehicle    : car")
        print("OCR        : 95%")
        print("Status     : VALID")
        print("=" * 60)

    except Exception as e:

        db.rollback()
        print("❌ Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    create_demo_detection()