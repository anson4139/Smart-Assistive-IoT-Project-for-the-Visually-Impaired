from __future__ import annotations

import signal
import time
from typing import TYPE_CHECKING

from pi4.core.config import ALERT_VOICE_COOLDOWN_SEC, MAIN_LOOP_INTERVAL_SEC
from pi4.core.event_schema import Event
from pi4.core.logger import get_logger
from pi4.safety.vision import camera_capture, vision_safety

if TYPE_CHECKING:
    from pi4.voice.voice_output import VoiceOutput

LOGGER = get_logger("continuous_safety_monitor")


class ContinuousSafetyMonitor:
    """Runs an endless safety loop that prints detections and speaks alerts."""

    def __init__(
        self,
        alert_distance_m: float = 1.0,
        loop_interval: float | None = None,
        alert_cooldown: float | None = None,
        voice_output: VoiceOutput | None = None,
    ) -> None:
        self.alert_distance_m = alert_distance_m
        self.loop_interval = loop_interval or MAIN_LOOP_INTERVAL_SEC
        cooldown_source = alert_cooldown if alert_cooldown is not None else ALERT_VOICE_COOLDOWN_SEC
        self._alert_cooldown = max(cooldown_source, 0.0)
        if voice_output is not None:
            self._voice_output = voice_output
        else:
            from pi4.voice.voice_output import VoiceOutput

            self._voice_output = VoiceOutput()
        self._running = True
        self._last_voice_times: dict[str, float] = {}

    def _setup_signal_handlers(self) -> None:
        def stop(_signum: int, _frame: object | None) -> None:
            LOGGER.info("收到停止訊號，準備退出。")
            self._running = False

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)

    def _render_event(self, event: Event) -> str:
        label = event.object_label or event.type
        distance = (
            f"{event.distance_m:.2f} m" if event.distance_m is not None else "unknown"
        )
        severity = event.severity
        return f"[{severity}] {label} @ {distance}"

    def _speak_alert(self, event: Event) -> None:
        if (
            event.distance_m is None
            or event.distance_m > self.alert_distance_m
            or event.severity not in ("mid", "high", "critical")
        ):
            return
        label = event.object_label or event.type.split(".")[-1]
        if not self._should_speak(label):
            return
        voice_text = (
            f"警告：前方有 {label}，距離約 {event.distance_m:.1f} 公尺，請立即注意。"
        )
        self._voice_output.speak(voice_text, priority="high")

    def _should_speak(self, label: str) -> bool:
        now = time.monotonic()
        last_time = self._last_voice_times.get(label)
        if last_time is not None and now - last_time < self._alert_cooldown:
            return False
        self._last_voice_times[label] = now
        return True

    def _process_once(self) -> None:
        frame = camera_capture.get_frame()
        events = vision_safety.process_frame(frame)
        if not events:
            print("沒有偵測到任何事件。")
            return
        for event in events:
            print(self._render_event(event))
            self._speak_alert(event)

    def run(self) -> None:
        """Start the loop and keep running until interrupted."""
        print("啟動循環安全監測，按 Ctrl+C 停止。")
        LOGGER.info("Continuous safety monitor start")
        self._setup_signal_handlers()
        try:
            while self._running:
                if self._voice_output.is_busy():
                    time.sleep(self.loop_interval)
                    continue
                self._process_once()
                if self._voice_output.is_busy():
                    self._voice_output.wait_until_idle()
                time.sleep(self.loop_interval)
        except KeyboardInterrupt:
            # fallback if signal handler not triggered
            LOGGER.info("KeyboardInterrupt received, stopping monitor")
        finally:
            LOGGER.info("Continuous safety monitor end")


def main() -> None:
    monitor = ContinuousSafetyMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
