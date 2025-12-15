from __future__ import annotations

import random


def read_distance_mm() -> float:
    """Simulated VL53L0X reading in millimeters."""
    return random.uniform(50.0, 400.0)
