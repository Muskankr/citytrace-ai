from database.database import SessionLocal

from database.models import (
    Camera,
    VehicleDetection,
    Trajectory,
    TrafficAnalytics,
    Alert
)


def show_system_status():

    db = SessionLocal()

    try:

        print("=" * 70)
        print("SIH26127 SYSTEM STATUS")
        print("=" * 70)

        # ----------------------------------------------------
        # Database counts
        # ----------------------------------------------------

        camera_count = (
            db.query(Camera).count()
        )

        detection_count = (
            db.query(VehicleDetection).count()
        )

        trajectory_count = (
            db.query(Trajectory).count()
        )

        analytics_count = (
            db.query(TrafficAnalytics).count()
        )

        alert_count = (
            db.query(Alert).count()
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print()
        print(
            f"📷 Cameras          : "
            f"{camera_count}"
        )

        print(
            f"🚗 Vehicle Detections: "
            f"{detection_count}"
        )

        print(
            f"🛣️ Trajectories      : "
            f"{trajectory_count}"
        )

        print(
            f"📊 Analytics Records : "
            f"{analytics_count}"
        )

        print(
            f"🚨 Alerts            : "
            f"{alert_count}"
        )

        # ----------------------------------------------------
        # Cameras
        # ----------------------------------------------------

        print()
        print("-" * 70)
        print("CAMERA NETWORK")
        print("-" * 70)

        cameras = (
            db.query(Camera)
            .order_by(Camera.camera_id)
            .all()
        )

        for camera in cameras:

            status = (
                "ACTIVE"
                if camera.is_active
                else "INACTIVE"
            )

            print(
                f"{camera.camera_id} | "
                f"{camera.name} | "
                f"{status}"
            )

        # ----------------------------------------------------
        # Plates
        # ----------------------------------------------------

        print()
        print("-" * 70)
        print("RECOGNIZED PLATES")
        print("-" * 70)

        detections = (
            db.query(VehicleDetection)
            .filter(
                VehicleDetection.plate_valid == True
            )
            .all()
        )

        unique_plates = sorted(
            set(
                d.plate_number
                for d in detections
                if d.plate_number
            )
        )

        if unique_plates:

            for plate in unique_plates:

                print(
                    f"🔤 {plate}"
                )

        else:

            print("No valid plates found.")

        # ----------------------------------------------------
        # Trajectories
        # ----------------------------------------------------

        print()
        print("-" * 70)
        print("TRAJECTORIES")
        print("-" * 70)

        trajectories = (
            db.query(Trajectory)
            .all()
        )

        if trajectories:

            for trajectory in trajectories:

                print(
                    f"🚗 {trajectory.plate_number} | "
                    f"{trajectory.route} | "
                    f"{trajectory.distance_km:.3f} km"
                )

        else:

            print("No trajectories found.")

        print()
        print("=" * 70)
        print("✅ SYSTEM STATUS COMPLETE")
        print("=" * 70)

    finally:

        db.close()


if __name__ == "__main__":

    show_system_status()