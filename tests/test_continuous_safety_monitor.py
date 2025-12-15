from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from pi4.core.event_schema import Event
from tests.continuous_safety_monitor import ContinuousSafetyMonitor


class DummyVoiceOutput:
    def __init__(self) -> None:
        self.spoken: list[str] = []

    def speak(self, text: str, priority: str = "mid") -> None:
        self.spoken.append((text, priority))


def _make_event(distance_m: float, severity: str, label: str) -> Event:
    return Event(
        event_id=str(uuid4()),
        ts=datetime.now(timezone.utc),
        type="vision.alert",
        source="camera",
        severity=severity,
        distance_m=distance_m,
        object_label=label,
    )


def test_alert_triggered_within_limit(monkeypatch, capsys) -> None:
    events = [_make_event(0.75, "high", "person")]
    monitor = ContinuousSafetyMonitor(
        alert_distance_m=1.0,
        loop_interval=0,
        voice_output=DummyVoiceOutput(),
    )
    monkeypatch.setattr(
        "pi4.safety.vision.camera_capture.get_frame", lambda: "frame"
    )
    monkeypatch.setattr(
        "pi4.safety.vision.vision_safety.process_frame", lambda frame: events
    )

    monitor._process_once()

    assert monitor._voice_output.spoken
    captured = capsys.readouterr()
    assert "[high] person" in captured.out


def test_no_alert_above_limit(monkeypatch) -> None:
    events = [_make_event(1.2, "mid", "car")]
    voice = DummyVoiceOutput()
    monitor = ContinuousSafetyMonitor(
        alert_distance_m=1.0,
        loop_interval=0,
        voice_output=voice,
    )
    monkeypatch.setattr(
        "pi4.safety.vision.camera_capture.get_frame", lambda: "frame"
    )
    monkeypatch.setattr(
        "pi4.safety.vision.vision_safety.process_frame", lambda frame: events
    )

    monitor._process_once()

    assert not voice.spoken


def test_run_stops_on_keyboard_interrupt(monkeypatch) -> None:
    voice = DummyVoiceOutput()
    monitor = ContinuousSafetyMonitor(voice_output=voice, loop_interval=0)
    counter = {"calls": 0}

    def fake_process() -> None:
        counter["calls"] += 1
        raise KeyboardInterrupt

    monkeypatch.setattr(monitor, "_process_once", fake_process)
    monitor.run()
    assert counter["calls"] == 1
