from __future__ import annotations

import pytest

from pi4.safety.vision import ncs_inference, vision_safety


def test_process_frame_generates_events(monkeypatch) -> None:
    fake_detection = ncs_inference.DetectedObject(
        label="person",
        bbox=(0, 0, 10, 100),
        confidence=0.9,
    )

    def fake_detect(frame):
        return [fake_detection]

    monkeypatch.setattr(ncs_inference, "detect_objects", fake_detect)
    events = vision_safety.process_frame(object())
    assert events
    assert events[0].type == "vision.person"
    assert events[0].source == "camera"


def run_tests_unit() -> bool:
    return pytest.main([__file__]) == 0
