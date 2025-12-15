from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

Severity = Literal["low", "mid", "high", "critical"]

VALID_SEVERITIES = {"low", "mid", "high", "critical"}

@dataclass
class Event:
    event_id: str
    ts: datetime
    type: str
    source: str
    severity: Severity
    distance_m: Optional[float] = None
    direction: Optional[str] = None
    object_label: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity: {self.severity}")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["ts"] = self.ts.isoformat()
        return data

    @classmethod
    def from_dict(cls, payload: dict) -> "Event":
        ts_value = payload.get("ts")
        if isinstance(ts_value, str):
            ts_value = datetime.fromisoformat(ts_value)
        return cls(
            event_id=payload["event_id"],
            ts=ts_value,
            type=payload["type"],
            source=payload["source"],
            severity=payload["severity"],
            distance_m=payload.get("distance_m"),
            direction=payload.get("direction"),
            object_label=payload.get("object_label"),
            extra=payload.get("extra", {}),
        )
