from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Alert, Camera
from api.schemas import AlertResponse

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


def convert_alert(
    alert: Alert,
    db: Session
) -> AlertResponse:

    camera = None

    if alert.camera_id:
        camera = (
            db.query(Camera)
            .filter(Camera.id == alert.camera_id)
            .first()
        )

    return AlertResponse(
        id=alert.id,
        plate_number=alert.plate_number,
        camera_id=camera.camera_id if camera else None,
        timestamp=alert.timestamp,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        latitude=alert.latitude,
        longitude=alert.longitude,
        is_resolved=alert.is_resolved,
    )


@router.get(
    "/",
    response_model=list[AlertResponse]
)
def get_alerts(
    db: Session = Depends(get_db)
):
    alerts = (
        db.query(Alert)
        .order_by(Alert.timestamp.desc())
        .all()
    )

    return [
        convert_alert(alert, db)
        for alert in alerts
    ]


@router.get(
    "/active",
    response_model=list[AlertResponse]
)
def get_active_alerts(
    db: Session = Depends(get_db)
):
    alerts = (
        db.query(Alert)
        .filter(Alert.is_resolved == False)
        .order_by(Alert.timestamp.desc())
        .all()
    )

    return [
        convert_alert(alert, db)
        for alert in alerts
    ]


@router.get(
    "/plate/{plate_number}",
    response_model=list[AlertResponse]
)
def get_alerts_by_plate(
    plate_number: str,
    db: Session = Depends(get_db)
):
    alerts = (
        db.query(Alert)
        .filter(Alert.plate_number == plate_number)
        .order_by(Alert.timestamp.desc())
        .all()
    )

    return [
        convert_alert(alert, db)
        for alert in alerts
    ]