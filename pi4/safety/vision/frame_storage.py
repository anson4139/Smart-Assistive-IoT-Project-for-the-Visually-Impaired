from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from pi4.core.config import IMG_DIR

IMG_DIR.mkdir(parents=True, exist_ok=True)
_latest_frame_name: Optional[str] = None


def save_frame(frame: "np.ndarray") -> Optional[str]:
    global _latest_frame_name
    if frame is None:
        return None
    if frame.ndim != 3:
        return None
    timestamp = datetime.now().strftime("img_%Y%m%d%H%M%S")
    target = IMG_DIR / f"{timestamp}.jpg"
    try:
        import cv2
    except ImportError:
        return None
    cv2.imwrite(str(target), frame)
    _latest_frame_name = target.name
    return target.name


def latest_frame_name() -> Optional[str]:
    return _latest_frame_name
