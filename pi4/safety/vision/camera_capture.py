from __future__ import annotations

from pi4.core.config import PLATFORM, USE_SIMULATED_SENSORS
from pi4.core.logger import get_logger
from pi4.safety.vision import camera_capture_pi, camera_capture_sim
from pi4.safety.vision.frame_storage import latest_frame_name, save_frame

LOGGER = get_logger("camera_capture")
_frame_source: str = "simulation"


def get_frame() -> "Frame":
    """Return a video frame depending on platform and simulation config."""
    global _frame_source
    if not USE_SIMULATED_SENSORS:
        try:
            frame = camera_capture_pi.get_frame()
            _frame_source = "hardware"
        except Exception as error:
            LOGGER.warning(
                "Hardware capture unavailable (%s), falling back to simulation.",
                error,
            )
            frame = camera_capture_sim.get_frame()
            _frame_source = "simulation"
    else:
        frame = camera_capture_sim.get_frame()
        _frame_source = "simulation"
    save_frame(frame)
    return frame


def get_latest_image_name() -> str | None:
    return latest_frame_name()


def last_frame_source() -> str:
    """Return the source of the most recently captured frame."""
    return _frame_source
