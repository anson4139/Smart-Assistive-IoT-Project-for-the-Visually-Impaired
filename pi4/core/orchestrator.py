from __future__ import annotations

import time
import uuid
import threading
from datetime import datetime, timezone
from typing import Iterable

import numpy as np

from pi4.core.analyzer import log_analysis
from pi4.core.config import (
    FRAME_BLACK_THRESHOLD,
    MAIN_LOOP_DURATION_SEC,
    MAIN_LOOP_INTERVAL_SEC,
    USE_CONVERSATION_LAYER,
    USE_UNDERSTANDING_LAYER,
)
from pi4.core.event_bus import EventBus
from pi4.core.event_schema import Event
from pi4.core.logger import get_logger
from pi4.llm import (conversation_chatgpt_client,
                     understanding_ollama_client)
from pi4.safety.cane_client import cane_safety, tof_receiver
from pi4.safety.vision import camera_capture, vision_safety
from pi4.voice.voice_output import VoiceOutput
from pi4.voice.line_api_message import LineNotifier

logger = get_logger("orchestrator")


def _frame_mean(frame: "np.ndarray" | None) -> float:
    if frame is None:
        return 0.0
    array = np.asarray(frame)
    if array.size == 0:
        return 0.0
    return float(array.mean())


def _frame_is_blank(frame: "np.ndarray" | None) -> bool:
    return _frame_mean(frame) <= FRAME_BLACK_THRESHOLD

class Orchestrator:
    def __init__(self) -> None:
        self.bus = EventBus()
        self.voice = VoiceOutput()
        self.recent_camera_events: list[Event] = []
        self.recent_cane_events: list[Event] = []
        self.recent_danger_events: list[Event] = []
        self.recent_danger_events: list[Event] = []
        self.bus.subscribe("danger.events", self._collect_danger_event)
        self.line_notifier = LineNotifier()

    def _wait_for_voice_idle(self) -> None:
        if self.voice.is_busy():
            logger.info("Voice output busy; pausing safety loop until idle")
            self.voice.wait_until_idle()
            logger.info("Voice output idle; resuming safety loop")

    def _collect_danger_event(self, topic: str, payload: Event) -> None:
        self.recent_danger_events.append(payload)
        window_limit = int(1 / max(MAIN_LOOP_INTERVAL_SEC, 0.01))
        self.recent_danger_events = self.recent_danger_events[-window_limit:]

    # Add cooldown for LINE to prevent 429 errors
    _last_line_sent_time: float = 0.0
    _LINE_COOLDOWN_SEC: float = 3.0

    def _publish_events(self, topic: str, events: Iterable[Event]) -> None:
        for event in events:
            self.bus.publish(topic, event)
            if event.severity in ("mid", "high", "critical"):
                self.bus.publish("danger.events", event)

    def _process_safety(self) -> None:
        self._wait_for_voice_idle()
        
        # 1. Check ToF Trigger first (Event-Triggered)
        distance = tof_receiver.read_latest_distance()
        
        # If no trigger from ToF, and we are in event-triggered mode, we skip vision
        # Unless we want to support a "continuous mode" flag. 
        # For now, let's assume strict event-triggered for safety.
        if distance is None:
            # No trigger, do nothing
            return

        # 2. Trigger received! Wake up camera
        logger.info(f"Trigger received (dist={distance:.2f}m). Processing vision...")
        
        frame = camera_capture.get_frame()
        if _frame_is_blank(frame):
            logger.warning(
                "Captured frame looks blank (mean %.1f <= %.1f); skipping vision processing",
                _frame_mean(frame),
                FRAME_BLACK_THRESHOLD,
            )
            return
            
        camera_events = vision_safety.process_frame(frame)
        self._publish_events("camera.events", camera_events)
        self.recent_camera_events.extend(camera_events)
        
        # Generate Cane Event from the trigger distance
        cane_events = cane_safety.eval_distance(distance)
        self._publish_events("cane.events", cane_events)
        self.recent_cane_events.extend(cane_events)
        
        for event in camera_events + cane_events:
            if event.severity in ("mid", "high", "critical") and event.distance_m is not None:
                label_raw = event.object_label or event.type.split(".")[-1]
                
                # Simple translation map for fallback
                _TRANS_MAP = {
                    "person": "行人",
                    "car": "車輛",
                    "bike": "腳踏車",
                    "drop": "落差",
                    "step": "台階",
                    "step_down": "下台階",
                    "background": "背景",
                }
                label_zh = _TRANS_MAP.get(label_raw, label_raw)
                
                voice_text = (
                    f"前方有 {label_zh}，距離約 {event.distance_m:.1f} 公尺，請注意"
                )
                rewritten = voice_text
                used_ollama = False
                if USE_UNDERSTANDING_LAYER:
                    rewritten, used_ollama = understanding_ollama_client.rewrite_voice_text(
                        [event], voice_text
                    )
                source_tag = "Ollama" if used_ollama else "NAN"
                self.voice.speak(rewritten, priority="high", source=source_tag)
                self._wait_for_voice_idle()
                log_analysis(
                    camera_capture.get_latest_image_name(),
                    {
                        "voice_text": voice_text,
                        "voice_source": source_tag,
                        "rewritten_voice_text": rewritten,
                        "event": event.to_dict(),
                    },
                    "voice_distance_alert",
                    tags=["voice", "distance"],
                )
                
                # LINE Notification for Caregiver (High Severity only) with Cooldown
                # LINE Notification for Caregiver (High Severity only) with Cooldown
                now = time.time()
                if event.severity in ("high", "critical"):
                    if now - self._last_line_sent_time > self._LINE_COOLDOWN_SEC:
                        self._last_line_sent_time = now
                        
                        def _send_line_async(evt, txt):
                            try:
                                caregiver_text = understanding_ollama_client.rewrite_caregiver_text(
                                    [evt], txt
                                )
                                self.line_notifier.send(caregiver_text)
                            except Exception as e:
                                logger.error(f"Failed to send LINE alert: {e}")

                        # Run in background to avoid blocking detection loop
                        threading.Thread(
                            target=_send_line_async, 
                            args=(event, voice_text), 
                            daemon=True
                        ).start()

    def process_safety_once(self) -> None:
        """公開方法：單次執行 Safety Layer，方便外部調度。"""
        self._process_safety()

    def main_loop(self, duration_sec: float | None = None) -> None:
        logger.info("Orchestrator main loop start")
        duration = duration_sec if duration_sec is not None else MAIN_LOOP_DURATION_SEC
        deadline = time.monotonic() + duration
        cycle = 0
        while time.monotonic() < deadline:
            logger.debug("Main loop cycle %d", cycle)
            self._process_safety()
            if USE_UNDERSTANDING_LAYER and self.recent_danger_events:
                events_snapshot = list(self.recent_danger_events)
                msg = understanding_ollama_client.summarize_events(events_snapshot)
                if msg:
                    log_analysis(
                        camera_capture.get_latest_image_name(),
                        {
                            "summary": msg,
                            "events": [event.to_dict() for event in events_snapshot],
                        },
                        "understanding_summary",
                        tags=["voice", "understanding"],
                    )
                self.recent_danger_events.clear()
            if USE_CONVERSATION_LAYER:
                context = conversation_chatgpt_client.ConversationContext(
                    camera_events=self.recent_camera_events[-5:],
                    cane_events=self.recent_cane_events[-5:],
                    position="unknown",
                    time=datetime.now(timezone.utc),
                )
                query = "目前狀況如何？"
                reply = conversation_chatgpt_client.answer_question(
                    context, query)
                log_analysis(
                    camera_capture.get_latest_image_name(),
                    {"user_query": query, "reply": reply},
                    reply,
                    tags=["voice", "conversation"],
                )
                self.voice.speak(reply, priority="mid")
                self._wait_for_voice_idle()
            time.sleep(MAIN_LOOP_INTERVAL_SEC)
            cycle += 1
        logger.info("Orchestrator main loop end")

    def run_safety_simulation(self, iterations: int = 3) -> None:
        logger.info("Safety simulation start")
        for cycle in range(iterations):
            logger.debug("Simulation cycle %d", cycle)
            self._process_safety()
            for event in self.recent_danger_events:
                print(event)
            time.sleep(MAIN_LOOP_INTERVAL_SEC)
        logger.info("Safety simulation end")
