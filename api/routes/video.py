from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from pathlib import Path
import shutil
import uuid
import threading

from src.pipeline import main as run_pipeline

from src.processing_status import (
    create_job,
    update_job,
    get_job,
)

from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/video",
    tags=["Video Processing"],
)


UPLOAD_DIR = Path(
    "data/videos/uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def process_video(
    video_path: str,
    camera_code: str,
    job_id: str,
    filename: str,
):

    try:

        print()
        print("=" * 70)
        print("STARTING BACKGROUND AI VIDEO PROCESSING")
        print("=" * 70)
        print(f"Job    : {job_id}")
        print(f"Camera : {camera_code}")
        print(f"Video  : {video_path}")
        print("=" * 70)

        update_job(
            job_id=job_id,
            status="processing",
            message="AI pipeline started.",
            progress=5,
        )

        update_job(
            job_id=job_id,
            status="processing",
            message="Loading AI models and processing traffic video.",
            progress=10,
        )

        run_pipeline(
            video_path=video_path,
            camera_code=camera_code,
        )

        update_job(
            job_id=job_id,
            status="completed",
            message=(
                "AI video processing completed successfully."
            ),
            progress=100,
        )

        print()
        print("=" * 70)
        print("BACKGROUND VIDEO PROCESSING COMPLETE")
        print(f"Job : {job_id}")
        print("=" * 70)

    except Exception as error:

        print()
        print("=" * 70)
        print("BACKGROUND PROCESSING ERROR")
        print(f"Job   : {job_id}")
        print(f"Error : {error}")
        print("=" * 70)

        update_job(
            job_id=job_id,
            status="failed",
            message="AI video processing failed.",
            progress=0,
            error=str(error),
        )


@router.post("/upload")
async def upload_video(
    camera_code: str = Form(...),
    video: UploadFile = File(...),
):

    if not video.filename:
        raise HTTPException(
            status_code=400,
            detail="No video file selected.",
        )

    allowed_extensions = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
    }

    extension = Path(
        video.filename
    ).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video format. "
                "Use MP4, AVI, MOV or MKV."
            ),
        )

    job_id = uuid.uuid4().hex

    unique_name = (
        f"{job_id}{extension}"
    )

    output_path = (
        UPLOAD_DIR / unique_name
    )

    try:

        with output_path.open("wb") as buffer:

            shutil.copyfileobj(
                video.file,
                buffer,
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save video: {error}"
            ),
        )

    create_job(
        job_id=job_id,
        camera_code=camera_code,
        filename=video.filename,
    )

    thread = threading.Thread(
        target=process_video,
        args=(
            str(output_path),
            camera_code,
            job_id,
            video.filename,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "message": (
            "Video uploaded and "
            "AI processing started."
        ),
        "job_id": job_id,
        "camera_code": camera_code,
        "filename": video.filename,
        "saved_path": str(output_path),
        "status": "queued",
    }


@router.get("/status/{job_id}")
async def get_processing_status(
    job_id: str,
):

    job = get_job(job_id)

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="Processing job not found.",
        )

    return job

@router.get("/result")
async def get_processed_video():
    output_path = Path(
        "outputs/videos/master_pipeline.mp4"
    )

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed video is not available yet."
        )

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename="master_pipeline.mp4",
    )