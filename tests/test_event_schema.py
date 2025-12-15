from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pi4.core.event_schema import Event


def test_event_serialization_roundtrip() -> None:
    event = Event(
        event_id="evt-123",
        ts=datetime.now(timezone.utc),
        type="vision.person",
        source="camera",
        severity="mid",
        distance_m=1.2,
        direction="center",
        object_label="person",
    )
    serialized = event.to_dict()
    restored = Event.from_dict(serialized)
    assert restored.event_id == event.event_id
    assert restored.severity == event.severity
    assert restored.object_label == "person"

def test_event_from_dict_with_label() -> None:
    payload = {
        "event_id": "evt-321",
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "vision.car",
        "source": "camera",
        "severity": "high",
        "distance_m": 3.4,
        "direction": "left",
        "object_label": "car",
    }

    event = Event.from_dict(payload)
    assert event.event_id == "evt-321"
    assert event.object_label == "car"


def test_invalid_severity_raises() -> None:
    with pytest.raises(ValueError):
        Event(
            event_id="evt-999",
            ts=datetime.now(timezone.utc),
            type="vision.car",
            source="camera",
            severity="danger",
        )


def run_tests_unit() -> bool:
    return pytest.main([__file__]) == 0
