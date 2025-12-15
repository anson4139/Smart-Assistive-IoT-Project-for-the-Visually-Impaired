from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from pi4.core.config import SIM_TOF_DATA_PATH


class _SimulatedTof:
    def __init__(self) -> None:
        self._index = 0
        self._samples = self._load_samples()

    def _load_samples(self) -> List[float]:
        path = Path(SIM_TOF_DATA_PATH)
        if not path.exists():
            return [0.5, 0.3, 0.2, 0.1, 0.6]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [float(item) for item in data]
        except Exception:  # pragma: no cover
            return [0.5, 0.3, 0.2, 0.1, 0.6]

    def read_latest_distance(self) -> Optional[float]:
        if not self._samples:
            return None
        value = self._samples[self._index % len(self._samples)]
        self._index += 1
        return value


_simulator = _SimulatedTof()


def read_latest_distance() -> Optional[float]:
    """Return the next simulated ToF distance in meters."""
    return _simulator.read_latest_distance()
