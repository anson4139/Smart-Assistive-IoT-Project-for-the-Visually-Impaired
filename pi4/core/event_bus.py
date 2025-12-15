from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List

Callback = Callable[[str, Any], None]

class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callback]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callback) -> None:
        """Register a callback to receive publications for a topic."""
        self._subscribers[topic].append(callback)

    def publish(self, topic: str, payload: Any) -> None:
        """Publish payload to all subscribers of topic."""
        for cb in list(self._subscribers.get(topic, [])):
            cb(topic, payload)

    def clear(self) -> None:
        """Clear all subscribers (useful in tests)."""
        self._subscribers.clear()
