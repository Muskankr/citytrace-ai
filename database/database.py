from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file
DATABASE_URL = "sqlite:///sih26127.db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()


def get_db():
    """
    Create a database session.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    """
    # Import models so SQLAlchemy knows about them
    from database.models import (
        Camera,
        VehicleDetection,
        Trajectory,
        TrafficAnalytics,
        Alert
    )

    Base.metadata.create_all(bind=engine)

    print("✅ Database tables created successfully.")


if __name__ == "__main__":
    create_tables()