from __future__ import annotations

import heapq
import threading
import time
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import pyttsx3

from pi4.core.logger import get_logger

PriorityLevels = Literal["high", "mid", "low"]

_PRIORITY_MAP: dict[PriorityLevels, int] = {
    "high": 0,
    "mid": 1,
    "low": 2,
}


LOGGER = get_logger("voice_output")

class VoiceOutput:
    def __init__(self) -> None:
        self._queue: list[tuple[int, int, str, str | None]] = []
        self._counter = 0
        self._lock = threading.Lock()
        self._busy = False
        from pi4.core.config import PYTTXS3_RATE, PYTTXS3_VOLUME
        self._rate = PYTTXS3_RATE
        self._volume = min(max(PYTTXS3_VOLUME, 0.0), 1.0)
        
        # Initialize engine once to avoid SAPI5 hangs
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            self._engine.setProperty("volume", self._volume)
        except Exception as e:
            LOGGER.error(f"Failed to initialize TTS engine: {e}")
            self._engine = None

    def speak(
        self, text: str, priority: PriorityLevels = "mid", source: str | None = None
    ) -> None:
        """Queue the text and immediately process based on priority."""
        if not text:
            return
        self._counter += 1
        level = _PRIORITY_MAP.get(priority, 1)
        heapq.heappush(self._queue, (level, self._counter, text, source))
        LOGGER.info(
            "Queued voice [%s]%s: %s",
            priority,
            _format_source_tag(source),
            text,
        )
        self._drain()

    def _drain(self) -> None:
        with self._lock:
            self._busy = True
            try:
                while self._queue:
                    priority, _, text, source = heapq.heappop(self._queue)
                    
                    try:
                        import os
                        import subprocess
                        if os.name == 'nt':
                            # Use PowerShell for reliable blocking TTS on Windows
                            # Escape single quotes in text
                            safe_text = text.replace("'", "''")
                            cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe_text}')"
                            subprocess.run(["powershell", "-c", cmd], check=True)
                        else:
                            # Upgrade to Edge-TTS for natural human voice (requires internet)
                            # Command: edge-tts --text "Hello" --write-media /tmp/tts.mp3 --voice zh-TW-HsiaoChenNeural
                            # Then play with mpg123
                            try:
                                # Check if edge-tts is available (user setup required)
                                tmp_audio = "/tmp/smart_cane_tts.mp3"
                                # Use python3 -m edge_tts to avoid PATH issues (since it installed into .local/bin)
                                cmd_gen = [
                                    "python3", "-m", "edge_tts",
                                    "--text", text,
                                    "--write-media", tmp_audio,
                                    "--voice", "zh-TW-HsiaoChenNeural"
                                ]
                                subprocess.run(cmd_gen, check=True, capture_output=True)
                                
                                cmd_play = ["mpg123", tmp_audio]
                                subprocess.run(cmd_play, check=True, capture_output=True)
                            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                                # Fallback to robotic espeak if edge-tts fails or offline
                                LOGGER.warning("Edge-TTS failed: %s, falling back to espeak", e)
                                cmd = ["espeak", "-v", "zh", "-s", "150", text] 
                                subprocess.run(cmd, check=False)
                        
                        LOGGER.info(
                            "Spoke voice [%s]%s: %s",
                            priority,
                            _format_source_tag(source),
                            text,
                        )
                    except Exception:
                        LOGGER.exception(
                            "Voice output failed [%s]%s: %s",
                            priority,
                            _format_source_tag(source),
                            text,
                        )
            finally:
                self._busy = False

    def is_busy(self) -> bool:
        with self._lock:
            return self._busy

    def wait_until_idle(self, timeout: float | None = None) -> bool:
        start = time.monotonic()
        while True:
            if not self.is_busy():
                return True
            if timeout is not None and time.monotonic() - start >= timeout:
                return False
            time.sleep(0.01)


def _format_source_tag(source: str | None) -> str:
    return f" [{source}]" if source else ""
