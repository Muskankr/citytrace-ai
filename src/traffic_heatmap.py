from typing import List, Dict, Any

from database.database import SessionLocal
from database.models import TrafficAnalytics, Camera


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Density above this value is considered a bottleneck.
BOTTLENECK_DENSITY_THRESHOLD = 5.0

# Vehicle count above this value also contributes
# to bottleneck detection.
BOTTLENECK_VEHICLE_THRESHOLD = 5


# ---------------------------------------------------------
# CONGESTION SCORE
# ---------------------------------------------------------

def calculate_congestion_score(
    density: float,
    vehicle_count: int,
    average_speed: float
) -> float:
    """
    Calculate a normalized congestion score from 0 to 100.
    Higher score = heavier traffic.
    """

    density_score = min(
        density / 10.0,
        1.0
    ) * 50

    vehicle_score = min(
        vehicle_count / 20.0,
        1.0
    ) * 30

    # Lower speed means higher congestion.
    if average_speed <= 0:
        speed_score = 20
    elif average_speed < 20:
        speed_score = 20
    elif average_speed < 40:
        speed_score = 10
    else:
        speed_score = 0

    score = density_score + vehicle_score + speed_score

    return round(min(score, 100), 2)


# ---------------------------------------------------------
# BOTTLENECK DETECTION
# ---------------------------------------------------------

def is_bottleneck(
    density: float,
    vehicle_count: int,
    congestion_level: str
) -> bool:
    """
    Determine whether a camera location is a traffic bottleneck.
    """

    if density >= BOTTLENECK_DENSITY_THRESHOLD:
        return True

    if vehicle_count >= BOTTLENECK_VEHICLE_THRESHOLD:
        return True

    if congestion_level.lower() in {
        "high",
        "critical"
    }:
        return True

    return False


# ---------------------------------------------------------
# HEATMAP DATA
# ---------------------------------------------------------

def generate_heatmap_data() -> List[Dict[str, Any]]:
    """
    Generate GIS-ready heatmap data from traffic analytics.
    """

    db = SessionLocal()

    try:

        analytics_records = (
            db.query(TrafficAnalytics)
            .order_by(
                TrafficAnalytics.timestamp.desc()
            )
            .all()
        )

        results = []

        # Keep latest analytics record for each camera.
        processed_cameras = set()

        for analytics in analytics_records:

            camera = (
                db.query(Camera)
                .filter(
                    Camera.id == analytics.camera_id
                )
                .first()
            )

            if not camera:
                continue

            if camera.camera_id in processed_cameras:
                continue

            processed_cameras.add(
                camera.camera_id
            )

            density = (
                analytics.traffic_density
                or 0
            )

            vehicle_count = (
                analytics.vehicle_count
                or 0
            )

            average_speed = (
                analytics.average_speed
                or 0
            )

            congestion_level = (
                analytics.congestion_level
                or "LOW"
            )

            score = calculate_congestion_score(
                density=density,
                vehicle_count=vehicle_count,
                average_speed=average_speed
            )

            bottleneck = is_bottleneck(
                density=density,
                vehicle_count=vehicle_count,
                congestion_level=congestion_level
            )

            results.append(
                {
                    "camera_id": camera.camera_id,
                    "camera_name": camera.name,
                    "latitude": camera.latitude,
                    "longitude": camera.longitude,
                    "road_name": camera.road_name,
                    "direction": camera.direction,

                    "vehicle_count": vehicle_count,
                    "traffic_density": density,
                    "average_speed": average_speed,

                    "congestion_level": congestion_level,
                    "congestion_score": score,

                    "incoming_count": (
                        analytics.incoming_count
                        or 0
                    ),

                    "outgoing_count": (
                        analytics.outgoing_count
                        or 0
                    ),

                    "bottleneck": bottleneck,

                    # Value used directly by
                    # frontend heatmap rendering.
                    "heat_intensity": round(
                        score / 100,
                        3
                    ),
                }
            )

        return results

    finally:
        db.close()


# ---------------------------------------------------------
# BOTTLENECK REPORT
# ---------------------------------------------------------

def get_bottlenecks() -> List[Dict[str, Any]]:
    """
    Return only locations currently classified
    as traffic bottlenecks.
    """

    heatmap_data = generate_heatmap_data()

    return [
        item
        for item in heatmap_data
        if item["bottleneck"]
    ]


# ---------------------------------------------------------
# PRINT REPORT
# ---------------------------------------------------------

def print_heatmap_report():

    heatmap_data = generate_heatmap_data()

    print()
    print("=" * 75)
    print("              TRAFFIC HEATMAP ANALYTICS")
    print("=" * 75)

    if not heatmap_data:

        print()
        print("No traffic analytics available.")
        return

    for item in heatmap_data:

        print()
        print(
            f"Camera           : {item['camera_id']}"
        )

        print(
            f"Road             : {item['road_name']}"
        )

        print(
            f"Vehicles         : {item['vehicle_count']}"
        )

        print(
            f"Density          : {item['traffic_density']}"
        )

        print(
            f"Average Speed    : "
            f"{item['average_speed']} km/h"
        )

        print(
            f"Congestion       : "
            f"{item['congestion_level']}"
        )

        print(
            f"Congestion Score : "
            f"{item['congestion_score']}/100"
        )

        print(
            f"Bottleneck       : "
            f"{'YES' if item['bottleneck'] else 'NO'}"
        )

        print(
            f"Heat Intensity    : "
            f"{item['heat_intensity']}"
        )

    print()
    print("=" * 75)

    bottlenecks = get_bottlenecks()

    print(
        f"Detected bottlenecks: "
        f"{len(bottlenecks)}"
    )

    print("=" * 75)


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":
    print_heatmap_report()