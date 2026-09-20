from datetime import datetime, timedelta

from database.database import SessionLocal
from database.models import (
    VehicleDetection,
    TrafficAnalytics,
    Camera
)


# ============================================================
# TRAFFIC ANALYTICS ENGINE
# ============================================================

def calculate_traffic_analytics():

    db = SessionLocal()

    try:

        print("=" * 70)
        print("SIH26127 TRAFFIC ANALYTICS ENGINE")
        print("=" * 70)

        # ----------------------------------------------------
        # Get all detections
        # ----------------------------------------------------

        detections = (
            db.query(VehicleDetection)
            .order_by(
                VehicleDetection.timestamp.asc()
            )
            .all()
        )

        if not detections:

            print("\n❌ No vehicle detections found.")

            return

        print(
            f"\n🔎 Total detections found: "
            f"{len(detections)}"
        )

        # ----------------------------------------------------
        # Process each camera
        # ----------------------------------------------------

        cameras = (
            db.query(Camera)
            .filter(
                Camera.is_active == True
            )
            .all()
        )

        for camera in cameras:

            camera_detections = [
                d for d in detections
                if d.camera_id == camera.id
            ]

            if not camera_detections:
                continue

            # ------------------------------------------------
            # Vehicle type counts
            # ------------------------------------------------

            car_count = sum(
                1
                for d in camera_detections
                if d.vehicle_type == "car"
            )

            motorcycle_count = sum(
                1
                for d in camera_detections
                if d.vehicle_type == "motorcycle"
            )

            bus_count = sum(
                1
                for d in camera_detections
                if d.vehicle_type == "bus"
            )

            truck_count = sum(
                1
                for d in camera_detections
                if d.vehicle_type == "truck"
            )

            vehicle_count = len(
                camera_detections
            )

            # ------------------------------------------------
            # Traffic density
            #
            # Prototype metric:
            # number of vehicles observed
            # ------------------------------------------------

            traffic_density = float(
                vehicle_count
            )

            # ------------------------------------------------
            # Congestion level
            # ------------------------------------------------

            if vehicle_count <= 2:

                congestion_level = "LOW"

            elif vehicle_count <= 5:

                congestion_level = "MEDIUM"

            elif vehicle_count <= 10:

                congestion_level = "HIGH"

            else:

                congestion_level = "SEVERE"

            # ------------------------------------------------
            # Direction counts
            # ------------------------------------------------

            incoming_count = sum(
                1
                for d in camera_detections
                if d.direction == camera.direction
            )

            outgoing_count = (
                vehicle_count - incoming_count
            )

            # ------------------------------------------------
            # Average speed
            #
            # Current detections don't contain
            # individual speed, so use 0 for now.
            # Trajectory engine will provide speed later.
            # ------------------------------------------------

            average_speed = 0.0

            # ------------------------------------------------
            # Create analytics record
            # ------------------------------------------------

            analytics = TrafficAnalytics(

                camera_id=camera.id,

                timestamp=datetime.utcnow(),

                vehicle_count=vehicle_count,

                car_count=car_count,

                motorcycle_count=motorcycle_count,

                bus_count=bus_count,

                truck_count=truck_count,

                traffic_density=traffic_density,

                average_speed=average_speed,

                congestion_level=congestion_level,

                incoming_count=incoming_count,

                outgoing_count=outgoing_count
            )

            db.add(analytics)

            print()
            print(
                f"📷 {camera.camera_id} | "
                f"Vehicles: {vehicle_count} | "
                f"Cars: {car_count} | "
                f"Bikes: {motorcycle_count} | "
                f"Bus: {bus_count} | "
                f"Truck: {truck_count}"
            )

            print(
                f"   Density: {traffic_density:.2f} | "
                f"Congestion: {congestion_level}"
            )

        db.commit()

        print()
        print("-" * 70)
        print("📊 TRAFFIC ANALYTICS SUMMARY")
        print("-" * 70)

        print(
            f"Processed cameras : "
            f"{len(cameras)}"
        )

        print(
            f"Total detections  : "
            f"{len(detections)}"
        )

        print()
        print(
            "✅ Traffic analytics generated successfully!"
        )

    except Exception as e:

        db.rollback()

        print()
        print("❌ ANALYTICS ERROR")
        print("-" * 70)
        print(e)

    finally:

        db.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    calculate_traffic_analytics()