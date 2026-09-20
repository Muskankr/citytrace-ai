from datetime import datetime

from database.database import SessionLocal
from database.models import VehicleDetection, Alert


# ============================================================
# DEMO BLACKLIST
# ============================================================

BLACKLISTED_PLATES = {
    "HR26XY9999",
    "DL01ZZ9999",
    "UP16XX9999",
}


# ============================================================
# BLACKLIST ALERT
# ============================================================

def check_blacklisted_vehicle(detection, db):

    if (
        detection.plate_number
        and detection.plate_number in BLACKLISTED_PLATES
    ):

        # Prevent duplicate alert for same detection
        existing = (
            db.query(Alert)
            .filter(
                Alert.plate_number == detection.plate_number,
                Alert.camera_id == detection.camera_id,
                Alert.alert_type == "BLACKLISTED_VEHICLE",
            )
            .first()
        )

        if existing:
            return False

        alert = Alert(
            plate_number=detection.plate_number,
            camera_id=detection.camera_id,
            timestamp=datetime.utcnow(),
            alert_type="BLACKLISTED_VEHICLE",
            severity="HIGH",
            message=(
                f"Blacklisted vehicle detected: "
                f"{detection.plate_number}"
            ),
            latitude=detection.latitude,
            longitude=detection.longitude,
            is_resolved=False,
        )

        db.add(alert)

        print(
            f"🚨 BLACKLIST ALERT → "
            f"{detection.plate_number}"
        )

        return True

    return False


# ============================================================
# LOW OCR CONFIDENCE ALERT
# ============================================================

def check_low_confidence(detection, db):

    if (
        detection.plate_number
        and detection.ocr_confidence is not None
        and detection.ocr_confidence < 0.50
    ):

        existing = (
            db.query(Alert)
            .filter(
                Alert.plate_number == detection.plate_number,
                Alert.camera_id == detection.camera_id,
                Alert.alert_type == "LOW_OCR_CONFIDENCE",
            )
            .first()
        )

        if existing:
            return False

        alert = Alert(
            plate_number=detection.plate_number,
            camera_id=detection.camera_id,
            timestamp=datetime.utcnow(),
            alert_type="LOW_OCR_CONFIDENCE",
            severity="MEDIUM",
            message=(
                f"Low OCR confidence for "
                f"{detection.plate_number}"
            ),
            latitude=detection.latitude,
            longitude=detection.longitude,
            is_resolved=False,
        )

        db.add(alert)

        print(
            f"⚠️ LOW OCR CONFIDENCE → "
            f"{detection.plate_number}"
        )

        return True

    return False


# ============================================================
# ALERT ENGINE
# ============================================================

def run_alert_engine():

    db = SessionLocal()

    try:

        print("=" * 70)
        print("SIH26127 ALERT ENGINE")
        print("=" * 70)

        detections = (
            db.query(VehicleDetection)
            .all()
        )

        if not detections:
            print("\n❌ No detections available.")
            return

        alerts_created = 0

        for detection in detections:

            # Blacklist check
            if check_blacklisted_vehicle(
                detection,
                db
            ):
                alerts_created += 1

            # OCR confidence check
            if check_low_confidence(
                detection,
                db
            ):
                alerts_created += 1

        db.commit()

        print()
        print("-" * 70)
        print("🚨 ALERT SUMMARY")
        print("-" * 70)

        print(
            f"Detections checked : "
            f"{len(detections)}"
        )

        print(
            f"New alerts created : "
            f"{alerts_created}"
        )

        print()
        print("✅ Alert engine completed!")

    except Exception as e:

        db.rollback()

        print()
        print("❌ ALERT ENGINE ERROR")
        print("-" * 70)
        print(e)

    finally:
        db.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_alert_engine()