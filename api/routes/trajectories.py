from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Trajectory, Camera
from api.schemas import TrajectoryResponse

router = APIRouter(
    prefix="/trajectories",
    tags=["Trajectories"]
)


def convert_trajectory(
    trajectory: Trajectory,
    db: Session
) -> TrajectoryResponse:

    start_camera = None
    end_camera = None

    if trajectory.start_camera_id:
        start_camera = (
            db.query(Camera)
            .filter(Camera.id == trajectory.start_camera_id)
            .first()
        )

    if trajectory.end_camera_id:
        end_camera = (
            db.query(Camera)
            .filter(Camera.id == trajectory.end_camera_id)
            .first()
        )

    return TrajectoryResponse(
        id=trajectory.id,
        plate_number=trajectory.plate_number,
        track_id=trajectory.track_id,

        start_camera_id=(
            start_camera.camera_id
            if start_camera
            else None
        ),

        end_camera_id=(
            end_camera.camera_id
            if end_camera
            else None
        ),

        start_time=trajectory.start_time,
        end_time=trajectory.end_time,
        route=trajectory.route,
        distance_km=trajectory.distance_km,
        average_speed_kmh=trajectory.average_speed_kmh,
        direction=trajectory.direction,
        completed=trajectory.completed,
    )


@router.get(
    "/",
    response_model=list[TrajectoryResponse]
)
def get_trajectories(
    db: Session = Depends(get_db)
):
    trajectories = (
        db.query(Trajectory)
        .order_by(Trajectory.start_time.desc())
        .all()
    )

    return [
        convert_trajectory(trajectory, db)
        for trajectory in trajectories
    ]


@router.get(
    "/plate/{plate_number}",
    response_model=list[TrajectoryResponse]
)
def get_trajectories_by_plate(
    plate_number: str,
    db: Session = Depends(get_db)
):
    trajectories = (
        db.query(Trajectory)
        .filter(
            Trajectory.plate_number == plate_number
        )
        .order_by(Trajectory.start_time.asc())
        .all()
    )

    return [
        convert_trajectory(trajectory, db)
        for trajectory in trajectories
    ]