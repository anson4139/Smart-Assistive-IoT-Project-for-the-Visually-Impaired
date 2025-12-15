from __future__ import annotations

from pi4.core.config import MICROPHONE_INDEX
from pi4.core.logger import get_logger
from pi4.core.safety_support import SafetySupportRunner
from pi4.voice.line_api_message import LineNotifier
from pi4.voice.voice_control import VoiceCommandHandler

LOGGER = get_logger("voice_service")


class VoiceControlService:
    """Glue that keeps voice commands and safety support in sync."""

    def __init__(self, orchestrator=None) -> None:
        self._support = SafetySupportRunner(orchestrator=orchestrator)
        self._handler = VoiceCommandHandler(
            start_safety=self._support.start,
            stop_safety=self._support.stop,
            line_notifier=LineNotifier(),
            microphone_index=MICROPHONE_INDEX,
        )

    def start(self) -> None:
        """Start both voice listener and safety support (full active mode)."""
        LOGGER.info("Starting voice control service (Active Mode)")
        self._handler.start_listening()
        self._support.start()

    def start_standby(self) -> None:
        """Start only the voice listener (Standby Mode)."""
        LOGGER.info("Starting voice control service (Standby Mode)")
        self._handler.start_listening()

    def say_greeting(self) -> None:
        """Speak the greeting message."""
        self._handler.say_greeting()

    def stop(self) -> None:
        LOGGER.info("Stopping voice control service")
        self._handler.stop()
        self._support.stop()

    @property
    def is_safety_running(self) -> bool:
        return self._support.is_running

