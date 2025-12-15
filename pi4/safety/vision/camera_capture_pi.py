from __future__ import annotations

import platform

import cv2
import numpy as np

from pi4.core.config import CAMERA_DEVICE_INDEX
from pi4.core.logger import get_logger

logger = get_logger("camera_capture_pi")
_capture: cv2.VideoCapture | None = None


def _backend_candidates() -> list[tuple[str, int | None]]:
    system = platform.system()
    preferred: list[str] = []
    if system == "Windows":
        preferred.extend(["CAP_DSHOW", "CAP_MSMF"])
    if system in ("Linux", "Darwin"):
        preferred.append("CAP_V4L2")
    preferred.append("CAP_ANY")
    seen: set[str] = set()
    candidates: list[tuple[str, int | None]] = []
    for name in preferred:
        if name in seen:
            continue
        seen.add(name)
        value = getattr(cv2, name, None)
        if value is not None:
            candidates.append((name, value))
    candidates.append(("default", None))
    return candidates


def _ensure_capture() -> cv2.VideoCapture:
    global _capture
    if _capture is None or not _capture.isOpened():
        for backend_name, backend_flag in _backend_candidates():
            if backend_flag is None:
                candidate = cv2.VideoCapture(CAMERA_DEVICE_INDEX)
            else:
                try:
                    candidate = cv2.VideoCapture(CAMERA_DEVICE_INDEX, backend_flag)
                except TypeError:
                    # Older OpenCV on Pi (e.g. 3.2.0 from apt) does not support backend argument
                    # Fallback to simple default capture
                    logger.warning("OpenCV version too old for backend selection; falling back to default.")
                    candidate = cv2.VideoCapture(CAMERA_DEVICE_INDEX)
            if candidate.isOpened():
                logger.info(
                    "Opened camera %s with backend %s",
                    CAMERA_DEVICE_INDEX,
                    backend_name,
                )
                _capture = candidate
                break
            candidate.release()
            logger.debug(
                "Camera %s not available with backend %s",
                CAMERA_DEVICE_INDEX,
                backend_name,
            )
        if _capture is None or not _capture.isOpened():
            logger.error("Cannot open camera device %s", CAMERA_DEVICE_INDEX)
            raise RuntimeError(f"Cannot open camera {CAMERA_DEVICE_INDEX}")
    return _capture


def get_frame() -> "np.ndarray":
    """Capture a frame from Pi4 camera; raises if unavailable."""
    cap = _ensure_capture()
    ret, frame = cap.read()
    if not ret or frame is None:
        logger.error("Camera capture failed")
        raise RuntimeError("camera read failed")
    return frame
