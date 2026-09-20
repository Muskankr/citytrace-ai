from typing import List, Dict, Any


def interpolate_bbox(
    bbox1: List[float],
    bbox2: List[float],
    steps: int
) -> List[List[float]]:
    """
    Linearly interpolate bounding boxes between two frames.

    bbox format:
    [x1, y1, x2, y2]

    Example:
        frame 10 -> bbox A
        frame 14 -> bbox B

    Returns estimated boxes for intermediate frames.
    """

    if steps <= 1:
        return []

    results = []

    for i in range(1, steps):
        ratio = i / steps

        interpolated = [
            bbox1[j] + (bbox2[j] - bbox1[j]) * ratio
            for j in range(4)
        ]

        results.append(interpolated)

    return results


def interpolate_plate_observations(
    observations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Fill short gaps between plate detections for the same vehicle track.

    Expected observation format:

    {
        "frame": 100,
        "bbox": [x1, y1, x2, y2],
        "confidence": 0.85
    }

    Only short gaps are interpolated.

    IMPORTANT:
    Interpolated observations are NOT treated as real detector
    detections. They are marked with:
        "interpolated": True
    """

    if len(observations) < 2:
        return observations.copy()

    observations = sorted(
        observations,
        key=lambda x: x["frame"]
    )

    output = []

    for i in range(len(observations) - 1):

        current = observations[i]
        next_obs = observations[i + 1]

        output.append(current)

        current_frame = int(current["frame"])
        next_frame = int(next_obs["frame"])

        gap = next_frame - current_frame

        # Only interpolate small gaps.
        # Avoid creating fake boxes across large occlusions.
        if 1 < gap <= 8:

            interpolated_boxes = interpolate_bbox(
                current["bbox"],
                next_obs["bbox"],
                gap
            )

            for j, bbox in enumerate(interpolated_boxes, start=1):

                frame_number = current_frame + j

                output.append({
                    "frame": frame_number,
                    "bbox": bbox,
                    "confidence": 0.0,
                    "interpolated": True
                })

    # Add final real observation
    output.append(observations[-1])

    return sorted(
        output,
        key=lambda x: x["frame"]
    )


def get_real_observations(
    observations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Return only actual detector observations.
    """

    return [
        obs for obs in observations
        if not obs.get("interpolated", False)
    ]


def get_best_observation(
    observations: List[Dict[str, Any]]
) -> Dict[str, Any] | None:
    """
    Select the best REAL plate observation.

    Interpolated boxes are never preferred over real detections.
    """

    real = get_real_observations(observations)

    if not real:
        return None

    return max(
        real,
        key=lambda x: (
            float(x.get("quality", 0.0)),
            float(x.get("confidence", 0.0))
        )
    )