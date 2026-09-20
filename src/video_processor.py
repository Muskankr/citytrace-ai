import cv2
from pathlib import Path


def get_video_info(video_path: str):
    """
    Read basic information about a traffic video.
    """

    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    duration = frame_count / fps if fps > 0 else 0

    cap.release()

    return {
        "filename": path.name,
        "width": width,
        "height": height,
        "fps": round(fps, 2),
        "frame_count": frame_count,
        "duration_seconds": round(duration, 2),
    }


def read_video(video_path: str):

    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    try:
        while True:

            success, frame = cap.read()

            if not success:
                break

            yield frame

    finally:
        cap.release()


if __name__ == "__main__":
    video_path = "data/videos/sih_traffic.mp4"

    info = get_video_info(video_path)

    print("\n========== VIDEO INFORMATION ==========")
    print(f"Filename : {info['filename']}")
    print(f"Resolution: {info['width']} x {info['height']}")
    print(f"FPS      : {info['fps']}")
    print(f"Frames   : {info['frame_count']}")
    print(f"Duration : {info['duration_seconds']} seconds")
    print("=======================================\n")