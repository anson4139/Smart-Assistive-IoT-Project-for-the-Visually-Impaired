from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Iterable

from pi4.core.config import (CAR_APPROACHING_MIN_DISTANCE_M,
                             CAR_ACTUAL_HEIGHT_M,
                             DISTANCE_VOICE_BIAS_M,
                             PERSON_ACTUAL_HEIGHT_M,
                             PERSON_NEAR_DISTANCE_M,
                             VISION_FOCAL_LENGTH)
from pi4.core.event_schema import Event
from pi4.safety.vision import ncs_inference


def _actual_height_for_label(label: str) -> float:
    return {
        "person": PERSON_ACTUAL_HEIGHT_M,
        "car": CAR_ACTUAL_HEIGHT_M,
    }.get(label, PERSON_ACTUAL_HEIGHT_M)


def _estimate_distance(bbox: Iterable[int], label: str) -> float:
    x1, y1, x2, y2 = bbox
    height_px = max(1, y2 - y1)
    actual_height = _actual_height_for_label(label)
    if height_px <= 0:
        return 10.0
    distance = (actual_height * VISION_FOCAL_LENGTH) / height_px
    return max(0.2, distance + DISTANCE_VOICE_BIAS_M)


def _direction_from_bbox(bbox: Iterable[int], frame_width: int) -> str:
    x1, _, x2, _ = bbox
    center = (x1 + x2) / 2
    ratio = center / max(frame_width, 1)
    if ratio < 0.33:
        return "left"
    if ratio > 0.66:
        return "right"
    return "center"


def _determine_severity(obj: "ncs_inference.DetectedObject", distance: float) -> str:
    if obj.label == "car" and distance <= CAR_APPROACHING_MIN_DISTANCE_M:
        return "critical"
    if obj.label == "car":
        return "mid"
    if obj.label == "person" and distance <= PERSON_NEAR_DISTANCE_M:
        return "high"
    return "low"


def process_frame(frame) -> list[Event]:
    """Call `detect_objects` and translate detections into events."""
    camera_events: list[Event] = []
    frame_shape = getattr(frame, "shape", None)
    frame_height = frame_shape[0] if frame_shape else 480
    frame_width = frame_shape[1] if frame_shape else 640
    detections = ncs_inference.detect_objects(frame)
    for detection in detections:
        distance = _estimate_distance(detection.bbox, detection.label)
        direction = _direction_from_bbox(detection.bbox, frame_width)
        severity = _determine_severity(detection, distance)
        event = Event(
            event_id=str(uuid.uuid4()),
            ts=datetime.now(timezone.utc),
            type=f"vision.{detection.label}",
            source="camera",
            severity=severity,
            distance_m=distance,
            direction=direction,
            extra={"confidence": detection.confidence},
        )
        camera_events.append(event)
    return camera_events
