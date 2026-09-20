from datetime import datetime
from threading import Lock
from typing import Dict, Any


_jobs: Dict[str, Dict[str, Any]] = {}
_lock = Lock()


def create_job(job_id: str, camera_code: str, filename: str):
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "camera_code": camera_code,
            "filename": filename,
            "status": "queued",
            "message": "Video uploaded and waiting for AI processing.",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
        }


def update_job(
    job_id: str,
    status: str,
    message: str,
    progress: int | None = None,
    error: str | None = None,
):
    with _lock:
        if job_id not in _jobs:
            return

        _jobs[job_id]["status"] = status
        _jobs[job_id]["message"] = message

        if progress is not None:
            _jobs[job_id]["progress"] = max(
                0,
                min(100, progress)
            )

        if error:
            _jobs[job_id]["error"] = error

        if status == "processing":
            if _jobs[job_id]["started_at"] is None:
                _jobs[job_id]["started_at"] = (
                    datetime.utcnow().isoformat()
                )

        if status in {"completed", "failed"}:
            _jobs[job_id]["completed_at"] = (
                datetime.utcnow().isoformat()
            )


def get_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)

        if job is None:
            return None

        return dict(job)