from database.database import SessionLocal, create_tables
from database.models import Camera


def seed_cameras():

    # Make sure tables exist
    create_tables()

    db = SessionLocal()

    cameras = [
        Camera(
            camera_id="CAM001",
            name="Main Road Junction",
            latitude=28.8955,
            longitude=76.6066,
            road_name="Delhi Road",
            direction="North",
            location="Main Road Junction",
            is_active=True,
            source_type="REPLAY"
        ),

        Camera(
            camera_id="CAM002",
            name="Railway Crossing",
            latitude=28.9001,
            longitude=76.6120,
            road_name="Railway Road",
            direction="East",
            location="Railway Crossing",
            is_active=True,
            source_type="SIMULATED"
        ),

        Camera(
            camera_id="CAM003",
            name="Bus Stand Road",
            latitude=28.8932,
            longitude=76.5998,
            road_name="Bus Stand Road",
            direction="South",
            location="Bus Stand",
            is_active=True,
            source_type="SIMULATED"
        ),

        Camera(
            camera_id="CAM004",
            name="University Gate",
            latitude=28.8730,
            longitude=76.6250,
            road_name="University Road",
            direction="East",
            location="University Gate",
            is_active=True,
            source_type="SIMULATED"
        ),

        Camera(
            camera_id="CAM005",
            name="City Center",
            latitude=28.8950,
            longitude=76.6200,
            road_name="City Center Road",
            direction="West",
            location="City Center",
            is_active=True,
            source_type="SIMULATED"
        ),

        Camera(
            camera_id="CAM006",
            name="Highway Junction",
            latitude=28.9100,
            longitude=76.6350,
            road_name="NH-9 Connector",
            direction="North",
            location="Highway Junction",
            is_active=True,
            source_type="SIMULATED"
        )
    ]

    # Add cameras
    for camera in cameras:

        existing = (
            db.query(Camera)
            .filter(Camera.camera_id == camera.camera_id)
            .first()
        )

        if existing:
            print(
                f"⚠️ {camera.camera_id} already exists"
            )
        else:
            db.add(camera)
            print(
                f"✅ Added {camera.camera_id} - {camera.name}"
            )

    db.commit()
    db.close()

    print("\n🎉 Camera seeding completed!")


if __name__ == "__main__":
    seed_cameras()