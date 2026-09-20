from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import TrafficAnalytics, Camera
from api.schemas import AnalyticsResponse
from src.od_analytics import calculate_od_pairs, get_od_matrix
from src.traffic_heatmap import (
    generate_heatmap_data,
    get_bottlenecks,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


def convert_analytics(
    analytics: TrafficAnalytics,
    db: Session
) -> AnalyticsResponse:

    camera = None

    if analytics.camera_id:
        camera = (
            db.query(Camera)
            .filter(Camera.id == analytics.camera_id)
            .first()
        )

    return AnalyticsResponse(
        id=analytics.id,
        camera_id=camera.camera_id if camera else "",
        timestamp=analytics.timestamp,
        vehicle_count=analytics.vehicle_count,
        car_count=analytics.car_count,
        motorcycle_count=analytics.motorcycle_count,
        bus_count=analytics.bus_count,
        truck_count=analytics.truck_count,
        traffic_density=analytics.traffic_density,
        average_speed=analytics.average_speed,
        congestion_level=analytics.congestion_level,
        incoming_count=analytics.incoming_count,
        outgoing_count=analytics.outgoing_count,
    )


@router.get(
    "/",
    response_model=list[AnalyticsResponse]
)
def get_analytics(
    db: Session = Depends(get_db)
):
    analytics_records = (
        db.query(TrafficAnalytics)
        .order_by(TrafficAnalytics.timestamp.desc())
        .all()
    )

    return [
        convert_analytics(record, db)
        for record in analytics_records
    ]


@router.get(
    "/camera/{camera_id}",
    response_model=list[AnalyticsResponse]
)
def get_analytics_by_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):
    camera = (
        db.query(Camera)
        .filter(Camera.camera_id == camera_id)
        .first()
    )

    if not camera:
        return []

    analytics_records = (
        db.query(TrafficAnalytics)
        .filter(
            TrafficAnalytics.camera_id == camera.id
        )
        .order_by(TrafficAnalytics.timestamp.desc())
        .all()
    )

    return [
        convert_analytics(record, db)
        for record in analytics_records
    ]

@router.get("/od")
def get_origin_destination():
    """
    Return Origin-Destination traffic pairs.
    """
    return calculate_od_pairs()


@router.get("/od/matrix")
def get_origin_destination_matrix():
    """
    Return Origin-Destination traffic matrix.
    """
    return get_od_matrix()

@router.get("/heatmap")
def get_traffic_heatmap():
    """
    Return GIS-ready traffic heatmap data.
    """
    return generate_heatmap_data()


@router.get("/bottlenecks")
def get_traffic_bottlenecks():
    """
    Return detected traffic bottlenecks.
    """
    return get_bottlenecks()