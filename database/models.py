from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship

from database.database import Base


# ============================================================
# CAMERA TABLE
# ============================================================

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)

    camera_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(String(100), nullable=False)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    road_name = Column(String(200))

    direction = Column(String(50))

    location = Column(String(200))

    is_active = Column(Boolean, default=True)


    source_type = Column(
    String(30),
    nullable=False,
    default="SIMULATED"
)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationship
    detections = relationship(
        "VehicleDetection",
        back_populates="camera"
    )


# ============================================================
# VEHICLE DETECTION TABLE
# ============================================================

class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Vehicle tracking information
    track_id = Column(
        Integer,
        index=True
    )

    vehicle_type = Column(
        String(50)
    )

    # License plate
    plate_number = Column(
        String(30),
        index=True
    )

    ocr_confidence = Column(
        Float,
        default=0.0
    )

    plate_valid = Column(
        Boolean,
        default=False
    )

    plate_status = Column(
        String(50)
    )

    # Camera information
    camera_id = Column(
        Integer,
        ForeignKey("cameras.id"),
        nullable=False
    )

    # Location
    latitude = Column(Float)

    longitude = Column(Float)

    direction = Column(String(50))

    # Detection timestamp
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    # Optional frame number
    frame_number = Column(Integer)

    # Detection confidence
    vehicle_confidence = Column(
        Float,
        default=0.0
    )

    plate_detection_confidence = Column(
        Float,
        default=0.0
    )

    # Relationship
    camera = relationship(
        "Camera",
        back_populates="detections"
    )


# ============================================================
# TRAJECTORY TABLE
# ============================================================

class Trajectory(Base):
    __tablename__ = "trajectories"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Recognized vehicle
    plate_number = Column(
        String(30),
        index=True
    )

    # Track information
    track_id = Column(
        Integer,
        index=True
    )

    # Starting camera
    start_camera_id = Column(
        Integer,
        ForeignKey("cameras.id")
    )

    # Ending camera
    end_camera_id = Column(
        Integer,
        ForeignKey("cameras.id")
    )

    start_time = Column(
        DateTime
    )

    end_time = Column(
        DateTime
    )

    # Route information
    route = Column(
        Text
    )

    distance_km = Column(
        Float,
        default=0.0
    )

    average_speed_kmh = Column(
        Float,
        default=0.0
    )

    # Direction
    direction = Column(
        String(50)
    )

    # Status
    completed = Column(
        Boolean,
        default=False
    )


# ============================================================
# TRAFFIC ANALYTICS TABLE
# ============================================================

class TrafficAnalytics(Base):
    __tablename__ = "traffic_analytics"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    camera_id = Column(
        Integer,
        ForeignKey("cameras.id")
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    # Number of vehicles
    vehicle_count = Column(
        Integer,
        default=0
    )

    car_count = Column(
        Integer,
        default=0
    )

    motorcycle_count = Column(
        Integer,
        default=0
    )

    bus_count = Column(
        Integer,
        default=0
    )

    truck_count = Column(
        Integer,
        default=0
    )

    # Traffic measurements
    traffic_density = Column(
        Float,
        default=0.0
    )

    average_speed = Column(
        Float,
        default=0.0
    )

    congestion_level = Column(
        String(50)
    )

    # Direction-wise traffic
    incoming_count = Column(
        Integer,
        default=0
    )

    outgoing_count = Column(
        Integer,
        default=0
    )


# ============================================================
# ALERT TABLE
# ============================================================

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Vehicle involved
    plate_number = Column(
        String(30),
        index=True
    )

    camera_id = Column(
        Integer,
        ForeignKey("cameras.id")
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    # Alert information
    alert_type = Column(
        String(100)
    )

    severity = Column(
        String(50)
    )

    message = Column(
        Text
    )

    # Location
    latitude = Column(Float)

    longitude = Column(Float)

    # Alert status
    is_resolved = Column(
        Boolean,
        default=False
    )


# ============================================================
# BLACKLISTED VEHICLE TABLE
# ============================================================

class BlacklistedVehicle(Base):
    __tablename__ = "blacklisted_vehicles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    plate_number = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )

    reason = Column(
        String(200)
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )