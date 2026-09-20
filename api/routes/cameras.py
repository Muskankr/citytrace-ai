from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Camera
from api.schemas import CameraResponse


router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"]
)


@router.get("/", response_model=list[CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):
    camera = (
        db.query(Camera)
        .filter(Camera.camera_id == camera_id)
        .first()
    )

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Camera not found"
        )

    return camera