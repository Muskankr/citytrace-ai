from collections import Counter
from typing import Dict, List, Any

from database.database import SessionLocal
from database.models import Trajectory


def normalize_camera(camera) -> str:
    """
    Convert camera IDs into a consistent format.

    Examples:
        1       -> CAM001
        "1"     -> CAM001
        "CAM001" -> CAM001
    """

    if camera is None:
        return "UNKNOWN"

    camera = str(camera).strip().upper()

    if camera.startswith("CAM"):
        number = camera.replace("CAM", "")

        if number.isdigit():
            return f"CAM{int(number):03d}"

        return camera

    if camera.isdigit():
        return f"CAM{int(camera):03d}"

    return camera


def calculate_od_pairs() -> List[Dict[str, Any]]:
    """
    Calculate Origin-Destination pairs
    from completed vehicle trajectories.
    """

    db = SessionLocal()

    try:
        trajectories = (
            db.query(Trajectory)
            .filter(
                Trajectory.completed == True,
                Trajectory.start_camera_id.isnot(None),
                Trajectory.end_camera_id.isnot(None),
            )
            .all()
        )

        od_counter = Counter()

        for trajectory in trajectories:

            origin = normalize_camera(
                trajectory.start_camera_id
            )

            destination = normalize_camera(
                trajectory.end_camera_id
            )

            if origin == "UNKNOWN" or destination == "UNKNOWN":
                continue

            od_counter[(origin, destination)] += 1

        results = []

        for (origin, destination), count in od_counter.items():

            results.append(
                {
                    "origin": origin,
                    "destination": destination,
                    "vehicle_count": count,
                }
            )

        results.sort(
            key=lambda item: item["vehicle_count"],
            reverse=True
        )

        return results

    finally:
        db.close()


def get_od_matrix() -> Dict[str, Dict[str, int]]:
    """
    Create an Origin-Destination matrix.
    """

    od_pairs = calculate_od_pairs()

    matrix: Dict[str, Dict[str, int]] = {}

    for item in od_pairs:

        origin = item["origin"]
        destination = item["destination"]
        count = item["vehicle_count"]

        if origin not in matrix:
            matrix[origin] = {}

        matrix[origin][destination] = count

    return matrix


def print_od_report():

    od_pairs = calculate_od_pairs()

    print()
    print("=" * 70)
    print("              ORIGIN-DESTINATION ANALYTICS")
    print("=" * 70)

    if not od_pairs:

        print()
        print("No completed trajectories available.")
        return

    print()

    for item in od_pairs:

        print(
            f"{item['origin']} → {item['destination']} "
            f"| Vehicles: {item['vehicle_count']}"
        )

    print()
    print("=" * 70)
    print("OD MATRIX")
    print("=" * 70)

    matrix = get_od_matrix()

    # IMPORTANT:
    # sorted() now works because every camera ID
    # has been normalized to a string.

    origins = sorted(matrix.keys())

    for origin in origins:

        print()
        print(f"Origin: {origin}")

        destinations = sorted(
            matrix[origin].keys()
        )

        for destination in destinations:

            count = matrix[origin][destination]

            print(
                f"   → {destination}: "
                f"{count} vehicle(s)"
            )

    print()
    print("=" * 70)


if __name__ == "__main__":
    print_od_report()