from database.database import SessionLocal
from database.models import Trajectory


# ============================================================
# DEMO DATA
# ============================================================

DEMO_PLATE = "HR26AN7777"

DEMO_ROUTE = (
    "CAM001 → CAM006 → CAM002"
)


# ============================================================
# CREATE DEMO TRAJECTORY
# ============================================================

def create_demo_trajectory():

    db = SessionLocal()

    try:

        existing = (
            db.query(Trajectory)
            .filter(
                Trajectory.plate_number
                == DEMO_PLATE
            )
            .first()
        )

        if existing:

            print(
                "⚠️ Demo suspicious trajectory "
                "already exists."
            )

            print(
                f"Plate: {DEMO_PLATE}"
            )

            print(
                f"Route: {existing.route}"
            )

            return

        trajectory = Trajectory(

            plate_number=DEMO_PLATE,

            track_id=777,

            start_camera_id="CAM001",

            end_camera_id="CAM002",

            route=DEMO_ROUTE,

            distance_km=8.70,

            average_speed_kmh=62.50,

            direction="East",

            completed=True,
        )

        db.add(trajectory)

        db.commit()

        print()
        print("=" * 70)
        print("DEMO SUSPICIOUS TRAJECTORY CREATED")
        print("=" * 70)

        print(
            f"Plate : {DEMO_PLATE}"
        )

        print(
            f"Route : {DEMO_ROUTE}"
        )

        print(
            "Expected network path does not allow "
            "CAM001 → CAM006."
        )

        print("=" * 70)

    except Exception as error:

        db.rollback()

        print(
            "❌ Error creating demo trajectory:"
        )

        print(error)

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    create_demo_trajectory()