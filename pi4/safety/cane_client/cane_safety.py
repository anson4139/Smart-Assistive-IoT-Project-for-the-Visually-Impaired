from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from pi4.core.config import (DROP_MAX_DISTANCE_M, DROP_MIN_DISTANCE_M,
                             STEP_DOWN_MIN_HEIGHT_M, STEP_MIN_HEIGHT_M)
from pi4.core.event_schema import Event


def eval_distance(distance_m: float) -> List[Event]:
    """Evaluate a ToF distance and classify drop/step events."""
    if distance_m is None or distance_m <= 0:
        return []
    if distance_m <= DROP_MIN_DISTANCE_M:
        event_type = "tof.drop"
        severity = "critical"
    elif distance_m <= STEP_MIN_HEIGHT_M:
        event_type = "tof.step"
        severity = "mid"
    elif distance_m <= STEP_DOWN_MIN_HEIGHT_M:
        event_type = "tof.step_down"
        severity = "high"
    elif distance_m <= DROP_MAX_DISTANCE_M:
        event_type = "tof.drop"
        severity = "high"
    else:
        return []
    return [
        Event(
            event_id=str(uuid.uuid4()),
            ts=datetime.now(timezone.utc),
            type=event_type,
            source="tof",
            severity=severity,
            distance_m=distance_m,
            direction="down",
        )
    ]
