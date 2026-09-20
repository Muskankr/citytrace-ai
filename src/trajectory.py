from datetime import datetime

from sqlalchemy import and_

from database.database import SessionLocal
from database.models import (
    VehicleDetection,
    Trajectory,
    Camera
)


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS coordinates.
    Returns distance in kilometers.
    """

    from math import radians, sin, cos, sqrt, atan2

    earth_radius = 6371.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


# ============================================================
# FIND VEHICLE OBSERVATIONS
# ============================================================

def get_vehicle_observations(db, plate_number):
    """
    Get all valid observations of a particular plate.
    """

    detections = (
        db.query(VehicleDetection)
        .filter(
            and_(
                VehicleDetection.plate_number == plate_number,
                VehicleDetection.plate_valid == True
            )
        )
        .order_by(VehicleDetection.timestamp.asc())
        .all()
    )

    return detections


# ============================================================
# BUILD TRAJECTORY
# ============================================================

def build_trajectory(plate_number):

    db = SessionLocal()

    try:

        print("=" * 70)
        print("SIH26127 VEHICLE TRAJECTORY ENGINE")
        print("=" * 70)

        # Get observations
        detections = get_vehicle_observations(
            db,
            plate_number
        )

        # Need at least two cameras
        if len(detections) < 2:

            print(
                f"\n❌ Not enough observations "
                f"for {plate_number}"
            )

            return

        print(
            f"\n🔎 Found {len(detections)} "
            f"observations for {plate_number}"
        )

        # ----------------------------------------------------
        # Remove duplicate camera observations
        # ----------------------------------------------------

        unique_detections = []

        visited_cameras = set()

        for detection in detections:

            if detection.camera_id not in visited_cameras:

                unique_detections.append(detection)

                visited_cameras.add(
                    detection.camera_id
                )

        # Need at least two different cameras
        if len(unique_detections) < 2:

            print(
                "\n❌ Vehicle was not observed "
                "at multiple cameras."
            )

            return

        # ----------------------------------------------------
        # Start / End
        # ----------------------------------------------------

        first = unique_detections[0]
        last = unique_detections[-1]

        # ----------------------------------------------------
        # Calculate total distance
        # ----------------------------------------------------

        total_distance = 0.0

        for i in range(
            len(unique_detections) - 1
        ):

            current = unique_detections[i]

            next_detection = unique_detections[i + 1]

            distance = haversine_distance(
                current.latitude,
                current.longitude,
                next_detection.latitude,
                next_detection.longitude
            )

            total_distance += distance

        # ----------------------------------------------------
        # Calculate travel time
        # ----------------------------------------------------

        time_difference = (
            last.timestamp - first.timestamp
        )

        travel_seconds = (
            time_difference.total_seconds()
        )

        travel_minutes = (
            travel_seconds / 60
        )

        # ----------------------------------------------------
        # Calculate average speed
        # ----------------------------------------------------

        if travel_seconds > 0:

            average_speed = (
                total_distance
                / (travel_seconds / 3600)
            )

        else:

            average_speed = 0.0

        # ----------------------------------------------------
        # Camera route
        # ----------------------------------------------------

        camera_ids = []

        for detection in unique_detections:

            camera = (
                db.query(Camera)
                .filter(
                    Camera.id == detection.camera_id
                )
                .first()
            )

            if camera:

                camera_ids.append(
                    camera.camera_id
                )

        route = " → ".join(camera_ids)

        # ----------------------------------------------------
        # Check existing trajectory
        # ----------------------------------------------------

        existing = (
            db.query(Trajectory)
            .filter(
                Trajectory.plate_number
                == plate_number
            )
            .first()
        )

        if existing:

            trajectory = existing

            trajectory.track_id = first.track_id
            trajectory.start_camera_id = first.camera_id
            trajectory.end_camera_id = last.camera_id
            trajectory.start_time = first.timestamp
            trajectory.end_time = last.timestamp
            trajectory.route = route
            trajectory.distance_km = total_distance
            trajectory.average_speed_kmh = average_speed
            trajectory.direction = last.direction
            trajectory.completed = True

            print(
                "\n🔄 Existing trajectory updated."
            )

        else:

            trajectory = Trajectory(
                plate_number=plate_number,
                track_id=first.track_id,
                start_camera_id=first.camera_id,
                end_camera_id=last.camera_id,
                start_time=first.timestamp,
                end_time=last.timestamp,
                route=route,
                distance_km=total_distance,
                average_speed_kmh=average_speed,
                direction=last.direction,
                completed=True
            )

            db.add(trajectory)

            print(
                "\n✅ New trajectory created."
            )

        db.commit()

        # ----------------------------------------------------
        # DISPLAY RESULT
        # ----------------------------------------------------

        print()
        print("-" * 70)
        print("🚗 VEHICLE TRAJECTORY")
        print("-" * 70)

        print(
            f"Plate           : {plate_number}"
        )

        print(
            f"Start Camera    : "
            f"{camera_ids[0]}"
        )

        print(
            f"End Camera      : "
            f"{camera_ids[-1]}"
        )

        print(
            f"Route           : {route}"
        )

        print(
            f"Observations    : "
            f"{len(unique_detections)}"
        )

        print(
            f"Travel Time     : "
            f"{travel_minutes:.2f} minutes"
        )

        print(
            f"Distance        : "
            f"{total_distance:.3f} km"
        )

        print(
            f"Average Speed   : "
            f"{average_speed:.2f} km/h"
        )

        print(
            f"Direction       : "
            f"{last.direction}"
        )

        print(
            f"Status          : COMPLETED"
        )

        print()
        print(
            "🎉 Trajectory generation successful!"
        )

    except Exception as e:

        db.rollback()

        print()
        print("❌ TRAJECTORY ERROR")
        print("-" * 70)
        print(e)

    finally:

        db.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_trajectory(
        "HR26AB1234"
    )