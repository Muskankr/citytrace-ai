from datetime import datetime, timedelta

from database.database import SessionLocal
from database.models import Camera, TrafficAnalytics


DEMO_TRAFFIC = {
    "CAM001": {
        "vehicle_count": 3,
        "car_count": 2,
        "motorcycle_count": 1,
        "bus_count": 0,
        "truck_count": 0,
        "traffic_density": 1.5,
        "average_speed": 48.0,
        "congestion_level": "LOW",
        "incoming_count": 2,
        "outgoing_count": 1,
    },

    "CAM002": {
        "vehicle_count": 7,
        "car_count": 4,
        "motorcycle_count": 2,
        "bus_count": 1,
        "truck_count": 0,
        "traffic_density": 3.5,
        "average_speed": 35.0,
        "congestion_level": "MEDIUM",
        "incoming_count": 4,
        "outgoing_count": 3,
    },

    "CAM003": {
        "vehicle_count": 12,
        "car_count": 7,
        "motorcycle_count": 3,
        "bus_count": 1,
        "truck_count": 1,
        "traffic_density": 6.5,
        "average_speed": 24.0,
        "congestion_level": "HIGH",
        "incoming_count": 7,
        "outgoing_count": 5,
    },

    "CAM004": {
        "vehicle_count": 20,
        "car_count": 11,
        "motorcycle_count": 4,
        "bus_count": 3,
        "truck_count": 2,
        "traffic_density": 9.0,
        "average_speed": 12.0,
        "congestion_level": "CRITICAL",
        "incoming_count": 13,
        "outgoing_count": 7,
    },

    "CAM005": {
        "vehicle_count": 8,
        "car_count": 5,
        "motorcycle_count": 2,
        "bus_count": 1,
        "truck_count": 0,
        "traffic_density": 4.0,
        "average_speed": 32.0,
        "congestion_level": "MEDIUM",
        "incoming_count": 5,
        "outgoing_count": 3,
    },

    "CAM006": {
        "vehicle_count": 2,
        "car_count": 1,
        "motorcycle_count": 1,
        "bus_count": 0,
        "truck_count": 0,
        "traffic_density": 1.0,
        "average_speed": 52.0,
        "congestion_level": "LOW",
        "incoming_count": 1,
        "outgoing_count": 1,
    },
}


def create_demo_traffic():
    db = SessionLocal()

    try:
        cameras = db.query(Camera).all()

        if not cameras:
            print("❌ No cameras found in database.")
            return

        camera_map = {
            camera.camera_id: camera
            for camera in cameras
        }

        created = 0

        # Make this record newer than previous analytics
        demo_time = datetime.utcnow()

        for camera_id, data in DEMO_TRAFFIC.items():

            camera = camera_map.get(camera_id)

            if camera is None:
                print(
                    f"⚠️ Camera {camera_id} not found. Skipping."
                )
                continue

            analytics = TrafficAnalytics(
                camera_id=camera.id,
                timestamp=demo_time + timedelta(
                    seconds=created
                ),
                vehicle_count=data["vehicle_count"],
                car_count=data["car_count"],
                motorcycle_count=data["motorcycle_count"],
                bus_count=data["bus_count"],
                truck_count=data["truck_count"],
                traffic_density=data["traffic_density"],
                average_speed=data["average_speed"],
                congestion_level=data["congestion_level"],
                incoming_count=data["incoming_count"],
                outgoing_count=data["outgoing_count"],
            )

            db.add(analytics)
            created += 1

        db.commit()

        print()
        print("=" * 70)
        print("       DEMO TRAFFIC DATA CREATED")
        print("=" * 70)

        for camera_id, data in DEMO_TRAFFIC.items():
            print(
                f"{camera_id} | "
                f"Vehicles: {data['vehicle_count']:>2} | "
                f"Density: {data['traffic_density']:>4} | "
                f"{data['congestion_level']}"
            )

        print("=" * 70)
        print(f"✅ Created {created} traffic analytics records.")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_demo_traffic()