from __future__ import annotations

from pathlib import Path

import numpy as np

from pi4.core.config import SIM_VIDEO_PATH


def get_frame() -> "np.ndarray":
    """Return a frame from the configured video or a placeholder."""
    video_path = Path(SIM_VIDEO_PATH)
    if not video_path.exists():
        return np.zeros((480, 640, 3), dtype=np.uint8)
    try:
        import cv2
    except ImportError:
        return np.zeros((480, 640, 3), dtype=np.uint8)
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        return np.zeros((480, 640, 3), dtype=np.uint8)
    return frame
