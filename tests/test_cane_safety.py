from __future__ import annotations

import pytest

from pi4.safety.cane_client import cane_safety


def test_drop_event_critical() -> None:
    events = cane_safety.eval_distance(0.04)
    assert events and events[0].type == "tof.drop"
    assert events[0].severity == "critical"


def test_step_down_event_high() -> None:
    events = cane_safety.eval_distance(0.18)
    assert events and events[0].type == "tof.step_down"
    assert events[0].severity == "high"


def test_no_event_when_safe() -> None:
    assert cane_safety.eval_distance(1.5) == []


def run_tests_unit() -> bool:
    return pytest.main([__file__]) == 0
