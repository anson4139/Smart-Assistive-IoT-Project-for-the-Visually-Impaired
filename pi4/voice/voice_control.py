from __future__ import annotations

import logging
import threading
import time
import queue
from collections.abc import Iterable, Iterator
from typing import Callable, Iterable as _Iterable

from pi4.core.config import LANGUAGE_CODE, WAKE_WORDS
from pi4.core.logger import get_logger
from pi4.voice.line_api_message import LineNotifier

try:
    import speech_recognition as sr  # type: ignore
except ImportError:  # pragma: no cover
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

LOGGER = get_logger("voice_control")


class TTSWorker(threading.Thread):
    """Dedicated thread for TTS to avoid blocking main thread or listener thread."""
    
    def __init__(self):
        super().__init__(name="TTSWorker", daemon=True)
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        
    def speak(self, text: str):
        self._queue.put(text)
        
    def stop(self):
        self._stop_event.set()
        self._queue.put(None)  # Sentinel
        
    def run(self):
        LOGGER.info("TTS Worker started")
        engine = None
        if pyttsx3:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
            except Exception as e:
                LOGGER.error("Failed to init TTS engine in worker: %s", e)
        
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=1.0)
                if text is None:
                    break
                
                if engine:
                    try:
                        print(f"Voice: {text}")
                        engine.say(text)
                        engine.runAndWait()
                    except Exception as e:
                        LOGGER.error("TTS error: %s", e)
                else:
                    LOGGER.warning("TTS engine not available, skipping: %s", text)
                    
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                LOGGER.exception("TTS Worker exception: %s", e)
        
        LOGGER.info("TTS Worker stopped")


class VoiceCommandHandler:
    """Listen for voice commands and dispatch mapped callbacks."""

    _COMMAND_KEYWORDS: dict[str, tuple[str, ...]] = {
        "start_safety": (
            "啟動行人輔助",
            "開始行人輔助",
            "開啟行人輔助",
            "safety support",
        ),
        "stop_safety": (
            "關閉行人輔助",
            "停止行人輔助",
            "停止 safety",
        ),
        "report_departure": ("我出發了", "出發", "開始旅程"),
        "report_arrival": ("我已經安全到達", "我到了", "安全抵達"),
    }

    def __init__(
        self,
        start_safety: Callable[[], None],
        stop_safety: Callable[[], None],
        line_notifier: LineNotifier | None = None,
        simulated_inputs: _Iterable[str] | None = None,
        listen_timeout: float = 5.0,
        microphone_index: int | None = None,
    ) -> None:
        self._start_safety_callback = start_safety
        self._stop_safety_callback = stop_safety
        self._line_notifier = line_notifier or LineNotifier()
        self._simulated_inputs: Iterator[str] | None = (
            iter(simulated_inputs) if simulated_inputs is not None else None
        )
        self._listen_timeout = listen_timeout
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._recognizer = sr.Recognizer() if sr else None
        
        # Microphone setup
        self._microphone_index = microphone_index
        self._microphone = self._build_microphone() if sr else None
        
        self._handlers: dict[str, Callable[[], None]] = {
            "start_safety": self._handle_start_safety,
            "stop_safety": self._handle_stop_safety,
            "report_departure": self._handle_report_departure,
            "report_arrival": self._handle_report_arrival,
        }
        
        # State management
        self._mode = "STANDBY"  # STANDBY or ACTIVE
        self._fail_count = 0
        
        # Initialize TTS Worker
        self._tts_worker = TTSWorker()
        self._tts_worker.start()
        
        self._list_microphones()

    def _list_microphones(self):
        if sr:
            print("\n=== Available Microphones ===")
            try:
                mics = sr.Microphone.list_microphone_names()
                for i, mic_name in enumerate(mics):
                    print(f"[{i}] {mic_name}")
            except Exception as e:
                print(f"Error listing microphones: {e}")
            print("=============================\n")

    def _build_microphone(self):
        if sr:
            if self._microphone_index is not None:
                LOGGER.info("Using microphone index: %s", self._microphone_index)
                return sr.Microphone(device_index=self._microphone_index)
            return sr.Microphone()
        return None

    def _speak(self, text: str) -> None:
        self._tts_worker.speak(text)

    def start_listening(self) -> None:
        if self._thread and self._thread.is_alive():
            LOGGER.debug("Voice listener already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop,
            name="VoiceCommandListener",
            daemon=True,
        )
        self._thread.start()
        LOGGER.info("Voice listener started")

    def stop(self) -> None:
        self._stop_event.set()
        self._tts_worker.stop()
        
        thread = self._thread
        self._thread = None
        if thread is not None:
            thread.join(timeout=1.0)
            LOGGER.info("Voice listener stopped")

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def say_greeting(self) -> None:
        self._speak("你好，我是您的智慧導盲犬助理。請說「啟動行人輔助」來開始。")

    def _listen_loop(self) -> None:
        LOGGER.info("Voice listener loop running")
        print("DEBUG: 語音監聽迴圈已啟動 (請確認麥克風已連接)")
        while not self._stop_event.is_set():
            try:
                text = self._listen_once()
            except Exception as exc:
                LOGGER.exception("Voice listening failed: %s", exc)
                text = None
                time.sleep(0.5)
            
            if text:
                # Success
                self._fail_count = 0
                print(f"DEBUG: 聽到語音內容: '{text}'")
                self._dispatch_command(text)
            else:
                # Failure (Timeout or Unknown)
                if self._mode == "ACTIVE":
                    self._fail_count += 1
                    print(f"DEBUG: 沒聽到指令 ({self._fail_count}/3)")
                    if self._fail_count >= 3:
                        self._speak("太久沒有收到指令，切換回待機模式")
                        self._handle_stop_safety()
                    else:
                        self._speak("我沒聽清楚，請再說一次")
                
            if self._simulated_inputs is not None and self._stop_event.is_set():
                break

    def _listen_once(self) -> str | None:
        if self._simulated_inputs is not None:
            try:
                value = next(self._simulated_inputs)
                time.sleep(0.05)
                LOGGER.debug("Simulated voice input: %s", value)
                return value
            except StopIteration:
                self._stop_event.set()
                return None
        if not self._recognizer or not self._microphone:
            time.sleep(0.25)
            return None
        try:
            with self._microphone as source:
                if self._mode == "ACTIVE":
                    print("DEBUG: [Active] 正在聆聽... (請下指令)")
                else:
                    print("DEBUG: [Standby] 正在聆聽... (等待喚醒詞: 啟動行人輔助)")
                    
                # self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(
                    source,
                    timeout=self._listen_timeout,
                    phrase_time_limit=5,
                )
            print("DEBUG: 正在辨識...")
            return self._recognizer.recognize_google(audio, language=LANGUAGE_CODE)
        except sr.WaitTimeoutError:
            print("DEBUG: 聆聽逾時")
            return None
        except sr.UnknownValueError:
            LOGGER.debug("Voice input not understood")
            print("DEBUG: 無法辨識內容")
            return None
        except sr.RequestError as exc:
            LOGGER.warning("Voice recognition request error: %s", exc)
            print(f"DEBUG: Google 語音辨識連線錯誤: {exc}")
            return None

    def _dispatch_command(self, text: str) -> None:
        normalized = self._normalize_text(text)
        for command, keywords in self._COMMAND_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                LOGGER.info("dispatching command [%s] from text: %s", command, text)
                handler = self._handlers.get(command)
                if handler:
                    handler()
                return # Command found and executed

        # If in active mode and no command matched
        if self._mode == "ACTIVE":
             self._speak("抱歉，我不知道這個指令")

    def _normalize_text(self, text: str) -> str:
        text = text.strip().lower()
        for wake in WAKE_WORDS:
            text = text.replace(wake.lower(), "").strip()
        return text

    def _handle_start_safety(self) -> None:
        if self._mode != "ACTIVE":
            self._mode = "ACTIVE"
            self._fail_count = 0
            self._speak("行人輔助已啟動")
            self._start_safety_callback()

    def _handle_stop_safety(self) -> None:
        if self._mode != "STANDBY":
            self._mode = "STANDBY"
            self._fail_count = 0
            self._speak("行人輔助已關閉")
            self._stop_safety_callback()

    def _handle_report_departure(self) -> None:
        self._speak("收到，回報出發")
        self._send_line_message("使用者已出發，行人輔助開啟中。")

    def _handle_report_arrival(self) -> None:
        self._speak("收到，回報抵達")
        self._send_line_message("使用者已安全抵達，行人輔助關閉。")
        # Usually arrival implies stopping safety too?
        # For now let's keep it separate or user can say "Stop Safety" after.

    def _send_line_message(self, message: str) -> None:
        if self._line_notifier:
            success = self._line_notifier.send(message)
            if not success:
                LOGGER.warning("LINE API message not sent: %s", message)
        else:
            LOGGER.debug("LINE API message disabled, would have sent: %s", message)