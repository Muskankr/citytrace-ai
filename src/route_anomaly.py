from typing import List, Dict, Any, Optional


# ============================================================
# CAMERA NETWORK
# ============================================================
#
# These are the allowed road connections in our prototype city.
#
# Example:
#
# CAM001 → CAM002 → CAM004
#
# If a vehicle suddenly appears on a camera that is not a
# valid next connection, the route can be flagged as suspicious.
#
# In the production system this graph would come from GIS /
# actual city road-network data.
# ============================================================

CAMERA_GRAPH = {
    "CAM001": ["CAM002", "CAM003"],
    "CAM002": ["CAM001", "CAM003", "CAM004"],
    "CAM003": ["CAM001", "CAM002", "CAM004", "CAM005"],
    "CAM004": ["CAM002", "CAM003", "CAM005", "CAM006"],
    "CAM005": ["CAM003", "CAM004", "CAM006"],
    "CAM006": ["CAM004", "CAM005"],
}


# ============================================================
# EXPECTED ROUTES
# ============================================================
#
# Demo routes for our prototype city.
#
# A real implementation would learn / configure these from
# the GIS road network and historical traffic data.
# ============================================================

EXPECTED_ROUTES = [
    ["CAM001", "CAM002"],
    ["CAM001", "CAM003"],
    ["CAM001", "CAM002", "CAM004"],
    ["CAM001", "CAM003", "CAM004"],
    ["CAM001", "CAM003", "CAM005"],
    ["CAM002", "CAM004"],
    ["CAM002", "CAM003", "CAM004"],
    ["CAM003", "CAM004", "CAM005"],
    ["CAM004", "CAM005", "CAM006"],
]


# ============================================================
# NORMALIZE ROUTE
# ============================================================

def normalize_route(route: Optional[str]) -> List[str]:
    """
    Convert route string into a clean camera list.

    Example:

        "CAM001 → CAM002 → CAM004"

    becomes:

        ["CAM001", "CAM002", "CAM004"]
    """

    if not route:
        return []

    route = route.replace("->", "→")

    cameras = []

    for camera in route.split("→"):
        camera = camera.strip().upper()

        if camera:
            cameras.append(camera)

    return cameras


# ============================================================
# CHECK CAMERA CONNECTION
# ============================================================

def is_valid_transition(
    current_camera: str,
    next_camera: str,
) -> bool:
    """
    Check whether movement from one camera to the next
    is allowed by the prototype camera network.
    """

    current_camera = current_camera.upper()
    next_camera = next_camera.upper()

    allowed = CAMERA_GRAPH.get(
        current_camera,
        []
    )

    return next_camera in allowed


# ============================================================
# FIND INVALID TRANSITIONS
# ============================================================

def find_invalid_transitions(
    cameras: List[str],
) -> List[Dict[str, Any]]:
    """
    Find suspicious jumps between consecutive cameras.
    """

    anomalies = []

    if len(cameras) < 2:
        return anomalies

    for index in range(len(cameras) - 1):

        current_camera = cameras[index]
        next_camera = cameras[index + 1]

        if not is_valid_transition(
            current_camera,
            next_camera,
        ):

            anomalies.append({
                "from_camera": current_camera,
                "to_camera": next_camera,
                "reason": (
                    f"No valid road-network connection "
                    f"from {current_camera} to {next_camera}."
                ),
            })

    return anomalies


# ============================================================
# CHECK ROUTE AGAINST EXPECTED ROUTES
# ============================================================

def route_matches_expected(
    cameras: List[str],
) -> bool:
    """
    Check whether the complete route matches one of the
    configured expected prototype routes.
    """

    for expected in EXPECTED_ROUTES:

        if cameras == expected:
            return True

    return False


# ============================================================
# ROUTE ANOMALY ANALYSIS
# ============================================================

def analyze_route(
    route: Optional[str],
) -> Dict[str, Any]:
    """
    Analyze a vehicle route and determine whether it is
    suspicious.

    Returns:

        {
            "suspicious": bool,
            "severity": str,
            "reason": str,
            "route": list,
            "invalid_transitions": list
        }
    """

    cameras = normalize_route(route)

    # --------------------------------------------------------
    # Not enough information
    # --------------------------------------------------------

    if len(cameras) < 2:

        return {
            "suspicious": False,
            "severity": "LOW",
            "reason": "Insufficient camera observations.",
            "route": cameras,
            "invalid_transitions": [],
        }

    # --------------------------------------------------------
    # Check unknown cameras
    # --------------------------------------------------------

    unknown_cameras = [
        camera
        for camera in cameras
        if camera not in CAMERA_GRAPH
    ]

    if unknown_cameras:

        return {
            "suspicious": True,
            "severity": "HIGH",
            "reason": (
                "Route contains unknown camera node(s): "
                + ", ".join(unknown_cameras)
            ),
            "route": cameras,
            "invalid_transitions": [],
        }

    # --------------------------------------------------------
    # Check invalid transitions
    # --------------------------------------------------------

    invalid_transitions = find_invalid_transitions(
        cameras
    )

    if invalid_transitions:

        transitions = []

        for item in invalid_transitions:

            transitions.append(
                f"{item['from_camera']} → "
                f"{item['to_camera']}"
            )

        return {
            "suspicious": True,
            "severity": "HIGH",
            "reason": (
                "Suspicious camera transition detected: "
                + ", ".join(transitions)
            ),
            "route": cameras,
            "invalid_transitions": invalid_transitions,
        }

    # --------------------------------------------------------
    # Check whether route is configured
    # --------------------------------------------------------

    if not route_matches_expected(cameras):

        return {
            "suspicious": True,
            "severity": "MEDIUM",
            "reason": (
                "Vehicle followed a valid camera connection "
                "but the complete route is not present in the "
                "configured expected-route patterns."
            ),
            "route": cameras,
            "invalid_transitions": [],
        }

    # --------------------------------------------------------
    # Normal route
    # --------------------------------------------------------

    return {
        "suspicious": False,
        "severity": "LOW",
        "reason": "Route matches the configured road network.",
        "route": cameras,
        "invalid_transitions": [],
    }


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def detect_route_anomaly(
    route: Optional[str],
) -> bool:
    """
    Simple True/False helper.
    """

    result = analyze_route(route)

    return result["suspicious"]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_routes = [
        "CAM001 → CAM002 → CAM004",
        "CAM001 → CAM006 → CAM002",
        "CAM002 → CAM004",
        "CAM003 → CAM006 → CAM001",
    ]

    print()
    print("=" * 70)
    print("        ROUTE ANOMALY ENGINE TEST")
    print("=" * 70)

    for route in test_routes:

        result = analyze_route(route)

        print()
        print(f"Route     : {route}")
        print(
            f"Suspicious: "
            f"{result['suspicious']}"
        )
        print(
            f"Severity  : "
            f"{result['severity']}"
        )
        print(
            f"Reason    : "
            f"{result['reason']}"
        )

    print()
    print("=" * 70)