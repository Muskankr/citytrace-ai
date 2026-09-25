from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import cameras
from api.routes import detections
from api.routes import trajectories
from api.routes import analytics
from api.routes import alerts
from api.routes import video


app = FastAPI(
    title="City-Wide AI Traffic Analytics API",
    description=(
        "AI-powered multi-camera ANPR, vehicle trajectory "
        "tracking and urban traffic analytics system."
    ),
    version="1.0.0"
)

# CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://citytrace-ai-dashboard.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API ROUTES

app.include_router(cameras.router)
app.include_router(detections.router)
app.include_router(trajectories.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(video.router)


# ROOT

@app.get("/")
def root():
    return {
        "message": "City-Wide AI Traffic Analytics API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }