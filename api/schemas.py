from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CameraResponse(BaseModel):
    id: int
    camera_id: str
    name: str
    latitude: float
    longitude: float
    road_name: str
    direction: str
    location: Optional[str] = None
    is_active: bool
    source_type: str

    class Config:
        from_attributes = True


class DetectionResponse(BaseModel):
    id: int
    track_id: Optional[int] = None
    vehicle_type: Optional[str] = None
    plate_number: Optional[str] = None
    ocr_confidence: Optional[float] = None
    plate_valid: bool
    plate_status: Optional[str] = None
    camera_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    direction: Optional[str] = None
    timestamp: datetime
    frame_number: Optional[int] = None
    vehicle_confidence: Optional[float] = None
    plate_detection_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class TrajectoryResponse(BaseModel):
    id: int
    plate_number: str
    track_id: Optional[int] = None
    start_camera_id: Optional[str] = None
    end_camera_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    route: Optional[str] = None
    distance_km: Optional[float] = None
    average_speed_kmh: Optional[float] = None
    direction: Optional[str] = None
    completed: bool

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    id: int
    camera_id: str
    timestamp: datetime
    vehicle_count: int
    car_count: int
    motorcycle_count: int
    bus_count: int
    truck_count: int
    traffic_density: float
    average_speed: float
    congestion_level: str
    incoming_count: int
    outgoing_count: int

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    plate_number: Optional[str] = None
    camera_id: Optional[str] = None
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_resolved: bool

    class Config:
        from_attributes = True