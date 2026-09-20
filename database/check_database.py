from database.database import SessionLocal

from database.models import (
    Camera,
    VehicleDetection,
    Trajectory,
    TrafficAnalytics,
    Alert
)


def check_database():

    db = SessionLocal()

    print("=" * 60)
    print("SIH26127 DATABASE STATUS")
    print("=" * 60)

    cameras = db.query(Camera).all()
    detections = db.query(VehicleDetection).all()
    trajectories = db.query(Trajectory).all()
    analytics = db.query(TrafficAnalytics).all()
    alerts = db.query(Alert).all()

    print(f"\n📷 Cameras       : {len(cameras)}")
    print(f"🚗 Detections    : {len(detections)}")
    print(f"🛣️ Trajectories  : {len(trajectories)}")
    print(f"📊 Analytics     : {len(analytics)}")
    print(f"🚨 Alerts        : {len(alerts)}")

    print("\n" + "-" * 60)
    print("CAMERAS")
    print("-" * 60)

    for camera in cameras:

        print(
            f"{camera.camera_id} | "
            f"{camera.name} | "
            f"{camera.road_name} | "
            f"({camera.latitude}, {camera.longitude})"
        )

    print("\n" + "-" * 60)
    print("DETECTIONS")
    print("-" * 60)

    for detection in detections:

        print(
            f"Track={detection.track_id} | "
            f"Vehicle={detection.vehicle_type} | "
            f"Plate={detection.plate_number or 'UNKNOWN'} | "
            f"OCR={detection.ocr_confidence:.2f} | "
            f"Status={detection.plate_status}"
        )

    db.close()


if __name__ == "__main__":
    check_database()