from datetime import datetime, timedelta

from database.database import SessionLocal
from database.models import VehicleDetection, Camera


def simulate_multi_camera():
    """
    Simulate the same vehicle being detected
    by multiple cameras across the city.
    """

    print("=" * 70)
    print("SIH26127 MULTI-CAMERA SIMULATION")
    print("=" * 70)

    db = SessionLocal()

    try:
        # ====================================================
        # SIMULATED OBSERVATIONS
        # ====================================================

        observations = [
            {
                "camera": "CAM001",
                "track_id": 101,
                "plate": "HR26AB1234",
                "vehicle_type": "car",
                "ocr_confidence": 0.92,
                "vehicle_confidence": 0.91,
                "plate_detection_confidence": 0.88,
                "status": "VALID",
                "minutes_after_start": 0
            },

            {
                "camera": "CAM002",
                "track_id": 205,
                "plate": "HR26AB1234",
                "vehicle_type": "car",
                "ocr_confidence": 0.95,
                "vehicle_confidence": 0.93,
                "plate_detection_confidence": 0.91,
                "status": "VALID",
                "minutes_after_start": 4
            },

            {
                "camera": "CAM004",
                "track_id": 318,
                "plate": "HR26AB1234",
                "vehicle_type": "car",
                "ocr_confidence": 0.91,
                "vehicle_confidence": 0.90,
                "plate_detection_confidence": 0.87,
                "status": "VALID",
                "minutes_after_start": 9
            }
        ]

        # Starting time of the simulated journey
        start_time = datetime.utcnow()

        print()

        # ====================================================
        # SAVE EACH OBSERVATION
        # ====================================================

        for observation in observations:

            # Find camera
            camera = (
                db.query(Camera)
                .filter(
                    Camera.camera_id == observation["camera"]
                )
                .first()
            )

            if camera is None:
                print(
                    f"❌ Camera not found: "
                    f"{observation['camera']}"
                )
                continue

            # Calculate detection timestamp
            detection_time = (
                start_time
                + timedelta(
                    minutes=observation["minutes_after_start"]
                )
            )

            # Create detection
            detection = VehicleDetection(
                track_id=observation["track_id"],

                vehicle_type=observation["vehicle_type"],

                plate_number=observation["plate"],

                ocr_confidence=observation["ocr_confidence"],

                plate_valid=True,

                plate_status=observation["status"],

                camera_id=camera.id,

                latitude=camera.latitude,

                longitude=camera.longitude,

                direction=camera.direction,

                timestamp=detection_time,

                vehicle_confidence=(
                    observation["vehicle_confidence"]
                ),

                plate_detection_confidence=(
                    observation["plate_detection_confidence"]
                )
            )

            db.add(detection)

            print(
                f"✅ {observation['camera']} → "
                f"{observation['plate']} → "
                f"Track {observation['track_id']}"
            )

        # Save everything
        db.commit()

        # ====================================================
        # DISPLAY SIMULATED JOURNEY
        # ====================================================

        print()
        print("-" * 70)
        print("🚗 SAME VEHICLE DETECTED ACROSS MULTIPLE CAMERAS")
        print("-" * 70)

        print("Plate       : HR26AB1234")
        print("Vehicle     : car")
        print("Route       : CAM001 → CAM002 → CAM004")
        print("Observations: 3")
        print("Duration    : 9 minutes")

        print()
        print("📍 Camera Journey:")
        print("   CAM001 → Main Road Junction")
        print("   CAM002 → Railway Crossing")
        print("   CAM004 → University Gate")

        print()
        print("✅ Multi-camera data saved successfully!")

    except Exception as e:

        db.rollback()

        print()
        print("❌ ERROR")
        print("-" * 70)
        print(e)

    finally:
        db.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    simulate_multi_camera()