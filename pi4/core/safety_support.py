from __future__ import annotations

import threading
import time

from pi4.core.config import MAIN_LOOP_INTERVAL_SEC
from pi4.core.logger import get_logger
from pi4.core.orchestrator import Orchestrator

LOGGER = get_logger("safety_support")


class SafetySupportRunner:
    """Minimal runner that keeps safety loops alive in a background thread."""

    def __init__(self, orchestrator: Orchestrator | None = None) -> None:
        self._orchestrator = orchestrator or Orchestrator()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return bool(thread and thread.is_alive())

    def start(self) -> None:
        if self.is_running:
            LOGGER.debug("Safety support already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="SafetySupportLoop", daemon=True
        )
        self._thread.start()
        LOGGER.info("Safety support thread started")

    def stop(self) -> None:
        if not self.is_running:
            LOGGER.debug("Safety support already stopped")
            return
        self._stop_event.set()
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=2.0)
        LOGGER.info("Safety support thread stopped")

    def _run_loop(self) -> None:
        LOGGER.info("Safety support loop running")
        try:
            while not self._stop_event.is_set():
                with self._lock:
                    self._orchestrator.process_safety_once()
                time.sleep(MAIN_LOOP_INTERVAL_SEC)
        finally:
            LOGGER.info("Safety support loop exiting")
