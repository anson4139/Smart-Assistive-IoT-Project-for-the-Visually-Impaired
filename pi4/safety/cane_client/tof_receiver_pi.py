from __future__ import annotations

import json
from typing import Optional

from pi4.core.config import TOF_BAUDRATE, TOF_SERIAL_PORT
from pi4.core.logger import get_logger

logger = get_logger("tof_receiver_pi")

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


def read_latest_distance() -> Optional[float]:
    """Try reading the latest ToF value from the Pi4 serial port."""
    if serial is None:
        logger.warning("serial module missing, cannot read Pi4 ToF")
        return None
    try:
        with serial.Serial(TOF_SERIAL_PORT, TOF_BAUDRATE, timeout=0.1) as ser:
            line = ser.readline().strip()
            if not line:
                return None
            data = json.loads(line)
            return float(data.get("distance_mm", 0)) / 1000
    except Exception as exc:  # pragma: no cover
        logger.debug("Exception reading ToF: %s", exc)
        return None
