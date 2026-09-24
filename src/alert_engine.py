from datetime import datetime

from database.database import SessionLocal
from database.models import (
    VehicleDetection,
    Trajectory,
    Alert,
    BlacklistedVehicle,
    Camera,
)
from src.route_anomaly import analyze_route


# ============================================================
# BLACKLIST ALERT
# ============================================================

def check_blacklisted_vehicle(detection, db):

    blacklisted = (
        db.query(BlacklistedVehicle)
        .filter(
            BlacklistedVehicle.plate_number
            == detection.plate_number,
            BlacklistedVehicle.is_active.is_(True),
        )
        .first()
    )

    if detection.plate_number and blacklisted:

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
            f"BLACKLIST ALERT -> "
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
            f"LOW OCR CONFIDENCE -> "
            f"{detection.plate_number}"
        )

        return True

    return False


# ============================================================
# SUSPICIOUS ROUTE ALERT
# ============================================================

def check_suspicious_route(trajectory, db):

    if not trajectory.route:
        return False

    result = analyze_route(
        trajectory.route
    )

    if not result["suspicious"]:
        return False

    latitude = None
    longitude = None
    camera = None

    if trajectory.start_camera_id:

        camera = (
            db.query(Camera)
            .filter(
                Camera.camera_id
                == str(trajectory.start_camera_id)
            )
            .first()
        )

    if camera:
        latitude = camera.latitude
        longitude = camera.longitude

    existing = (
        db.query(Alert)
        .filter(
            Alert.plate_number == trajectory.plate_number,
            Alert.alert_type == "SUSPICIOUS_ROUTE",
        )
        .first()
    )

    if existing:

        existing.camera_id = (
            camera.id if camera else None
        )

        existing.timestamp = (
            trajectory.start_time
            or datetime.utcnow()
        )

        existing.severity = result["severity"]

        existing.message = (
            f"{result['reason']} "
            f"Route: {trajectory.route}"
        )

        existing.latitude = latitude
        existing.longitude = longitude
        existing.is_resolved = False

        return True

    alert = Alert(
        plate_number=trajectory.plate_number,
        camera_id=camera.id if camera else None,
        timestamp=(
            trajectory.start_time
            or datetime.utcnow()
        ),
        alert_type="SUSPICIOUS_ROUTE",
        severity=result["severity"],
        message=(
            f"{result['reason']} "
            f"Route: {trajectory.route}"
        ),
        latitude=latitude,
        longitude=longitude,
        is_resolved=False,
    )

    db.add(alert)

    print(
        "SUSPICIOUS ROUTE ALERT -> "
        f"{trajectory.plate_number}"
    )

    print(
        f"Route: {trajectory.route}"
    )

    print(
        f"Reason: {result['reason']}"
    )

    return True


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

        trajectories = (
            db.query(Trajectory)
            .all()
        )

        alerts_created = 0

        # ----------------------------------------------------
        # VEHICLE DETECTION ALERTS
        # ----------------------------------------------------

        for detection in detections:

            if check_blacklisted_vehicle(
                detection,
                db
            ):
                alerts_created += 1

            if check_low_confidence(
                detection,
                db
            ):
                alerts_created += 1

        # ----------------------------------------------------
        # TRAJECTORY ALERTS
        # ----------------------------------------------------

        for trajectory in trajectories:

            if check_suspicious_route(
                trajectory,
                db
            ):
                alerts_created += 1

        db.commit()

        print()
        print("-" * 70)
        print("ALERT SUMMARY")
        print("-" * 70)

        print(
            f"Detections checked    : "
            f"{len(detections)}"
        )

        print(
            f"Trajectories checked  : "
            f"{len(trajectories)}"
        )

        print(
            f"New alerts created    : "
            f"{alerts_created}"
        )

        print()
        print("Alert engine completed!")

    except Exception as error:

        db.rollback()

        print()
        print("ALERT ENGINE ERROR")
        print("-" * 70)
        print(error)

    finally:

        db.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_alert_engine()