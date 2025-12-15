from __future__ import annotations

import json
import time
from typing import Optional

import serial
from pi4.core.config import TOF_BAUDRATE, TOF_SERIAL_PORT, USE_SIMULATED_SENSORS, TRIGGER_DISTANCE_MM
from pi4.core.logger import get_logger
from pi4.safety.cane_client import tof_receiver_sim

logger = get_logger("tof_receiver")

_serial_port: serial.Serial | None = None

def _init_serial() -> None:
    global _serial_port
    if _serial_port is not None:
        return
    try:
        _serial_port = serial.Serial(TOF_SERIAL_PORT, TOF_BAUDRATE, timeout=0.05)
        _serial_port.reset_input_buffer()
        logger.info(f"Opened ToF serial port: {TOF_SERIAL_PORT}")
    except Exception as e:
        logger.error(f"Failed to open ToF serial port: {e}")

def read_latest_distance() -> Optional[float]:
    """
    Return the most recent ToF reading, in meters.
    For event-triggered logic, this might return None if no trigger received.
    """
    if USE_SIMULATED_SENSORS:
        return tof_receiver_sim.read_latest_distance()
    
    _init_serial()
    if _serial_port is None:
        return None

    # Read all available lines, keep the last valid trigger
    last_valid_dist = None
    
    while _serial_port.in_waiting > 0:
        try:
            line = _serial_port.readline()
            if not line:
                continue
            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                continue
            
            # Parse JSON
            try:
                data = json.loads(text)
                
                # Check for explicit trigger event
                if data.get("event") == "trigger":
                    d_mm = data.get("d_mm")
                    if d_mm is not None:
                        last_valid_dist = float(d_mm) / 1000.0
                        logger.info(f"ToF Trigger received: {d_mm} mm")
                
                # Check for periodic 'tof' message but validation against distance threshold
                elif data.get("type") == "tof":
                    d_mm = data.get("d_mm")
                    if d_mm is not None:
                        # Only treat as trigger if within range (and not max value 8191)
                        if 0 < d_mm < TRIGGER_DISTANCE_MM:
                             last_valid_dist = float(d_mm) / 1000.0
                             logger.info(f"ToF Raw Trigger (valid distance): {d_mm} mm")

            except json.JSONDecodeError:
                pass
            except json.JSONDecodeError:
                pass
                
        except Exception as e:
            logger.error(f"Error reading from serial: {e}")
            
    return last_valid_dist
