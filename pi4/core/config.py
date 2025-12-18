from __future__ import annotations

import os
from pathlib import Path
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import platform

_system = platform.system().lower()
# Determine platform automatically unless overridden
if os.getenv("SMART_CANE_PLATFORM"):
    PLATFORM: Literal["desktop", "pi4"] = os.getenv("SMART_CANE_PLATFORM")  # type: ignore
else:
    # If explicitly linux/arm, assume pi4, otherwise desktop
    if "linux" in _system:
        PLATFORM: Literal["desktop", "pi4"] = "pi4"
    else:
        PLATFORM: Literal["desktop", "pi4"] = "desktop"

# always run real hardware to match the validated workflow
USE_SIMULATED_SENSORS: bool = False

# 相機設定
# Pi usually uses 0, Windows uses 1 (if 0 is webcam)
CAMERA_DEVICE_INDEX: int = 0 if PLATFORM == "pi4" else 1
SIM_VIDEO_PATH: str = os.getenv("SMART_CANE_SIM_VIDEO", "./data/demo_video.mp4")
FRAME_BLACK_THRESHOLD: float = float(os.getenv("SMART_CANE_FRAME_BLACK_THRESHOLD", "5.0"))

# ToF / UART
# Auto-switch port based on platform
if PLATFORM == "pi4":
    # Typical port for Pico on Pi
    TOF_SERIAL_PORT: str = "/dev/ttyACM0"
else:
    # Typical port for Pico on Windows
    TOF_SERIAL_PORT: str = "COM3"

TOF_BAUDRATE: int = 115200

SIM_TOF_DATA_PATH: str = os.getenv("SMART_CANE_SIM_TOF", "./data/tof_simulated.json")
SIM_TOF_INTERVAL_SEC: float = float(os.getenv("SMART_CANE_SIM_TOF_INTERVAL", "0.1"))

# Safety 門檻
PERSON_NEAR_DISTANCE_M: float = float(os.getenv("SMART_CANE_PERSON_NEAR", "2.5"))
CAR_APPROACHING_MIN_DISTANCE_M: float = float(os.getenv("SMART_CANE_CAR_APPROACHING", "3.0"))
VISION_FOCAL_LENGTH: float = float(os.getenv("SMART_CANE_VISION_FOCAL_LENGTH", "200"))
PERSON_ACTUAL_HEIGHT_M: float = float(os.getenv("SMART_CANE_PERSON_HEIGHT", "1.6"))
CAR_ACTUAL_HEIGHT_M: float = float(os.getenv("SMART_CANE_CAR_HEIGHT", "1.5"))
DISTANCE_VOICE_BIAS_M: float = float(os.getenv("SMART_CANE_DISTANCE_VOICE_BIAS", "0.0"))
CAR_APPROACHING_SPEED_THRESHOLD: float = float(os.getenv("SMART_CANE_CAR_SPEED", "1.0"))
DROP_MIN_DISTANCE_M: float = float(os.getenv("SMART_CANE_DROP_MIN", "0.05"))
DROP_MAX_DISTANCE_M: float = float(os.getenv("SMART_CANE_DROP_MAX", "0.40"))
STEP_MIN_HEIGHT_M: float = float(os.getenv("SMART_CANE_STEP_MIN", "0.10"))
STEP_DOWN_MIN_HEIGHT_M: float = float(os.getenv("SMART_CANE_STEP_DOWN", "0.20"))
MAIN_LOOP_DURATION_SEC: float = float(os.getenv("SMART_CANE_MAIN_LOOP_DURATION", "60"))
DANGER_EVENT_WINDOW_SEC: float = float(os.getenv("SMART_CANE_DANGER_WINDOW", "2.0"))
MAIN_LOOP_INTERVAL_SEC: float = float(os.getenv("SMART_CANE_MAIN_LOOP_INTERVAL", "0.02"))

# Trigger Logic
TRIGGER_DISTANCE_MM: int = int(os.getenv("SMART_CANE_TRIGGER_DISTANCE", "2500"))
TRIGGER_COOLDOWN_SEC: float = float(os.getenv("SMART_CANE_TRIGGER_COOLDOWN", "5.0"))

# LLM
LLM_TIMEOUT_SEC: float = 15.0
USE_UNDERSTANDING_LAYER: bool = True  # always run the understanding pipeline
OLLAMA_ENABLED: bool = True
# 若在 Pi 上執行且連線至 PC，請修改為 "http://<PC_IP>:11434"
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://10.241.180.128:11434")
# Use a smaller model for faster inference (27b is too slow for real-time)
OLLAMA_MODEL: str = "gemma2:9b"
# Increased timeout for network latency, though 9b should be fast
OLLAMA_REWRITE_TIMEOUT_SEC: float = 30.0
USE_CONVERSATION_LAYER: bool = os.getenv("SMART_CANE_USE_CONVERSATION", "false").lower() in ("1", "true", "yes")
OPENAI_ENABLED: bool = os.getenv("SMART_CANE_OPENAI_ENABLED", "true").lower() in ("1", "true", "yes")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE: str = os.getenv("SMART_CANE_OPENAI_BASE", "https://api.openai.com/v1")
OPENAI_MODEL: str = os.getenv("SMART_CANE_OPENAI_MODEL", "gpt-4.1-mini")
# OpenVINO defaults hard-coded for the desktop demo rig
OPENVINO_ENABLED: bool = True
OPENVINO_MODEL_XML: str | None = "models/person-detection-retail-0013.xml"
OPENVINO_MODEL_BIN: str | None = "models/person-detection-retail-0013.bin"
OPENVINO_DEVICE: str = "CPU"
OPENVINO_CONFIDENCE: float = 0.5
OPENVINO_LABELS: dict[int, str] = {0: "background", 1: "person", 2: "car", 3: "bike"}
PYTTXS3_RATE: int = int(os.getenv("SMART_CANE_TTS_RATE", "150"))
PYTTXS3_VOLUME: float = float(os.getenv("SMART_CANE_TTS_VOLUME", "1.0"))

# 語音
LANGUAGE_CODE: str = os.getenv("SMART_CANE_LANGUAGE", "zh-TW")
TTS_ENGINE: Literal["gtts", "local"] = os.getenv("SMART_CANE_TTS_ENGINE", "gtts")
TTS_TEMP_DIR: str = os.getenv("SMART_CANE_TTS_TEMP", "./tmp/tts/")
DESKTOP_AUDIO_OUTPUT_DEVICE: str | None = os.getenv("SMART_CANE_DESKTOP_AUDIO_DEVICE")
PI4_AUDIO_OUTPUT_DEVICE: str | None = os.getenv("SMART_CANE_PI4_AUDIO_DEVICE")
WAKE_WORDS: list[str] = [word.strip() for word in os.getenv("SMART_CANE_WAKE_WORDS", "小A,嗨小A").split(",") if word.strip()]
VOICE_SAMPLE_RATE: int = int(os.getenv("SMART_CANE_VOICE_SAMPLE_RATE", "16000"))
VOICE_CHUNK_MS: int = int(os.getenv("SMART_CANE_VOICE_CHUNK_MS", "30"))
MICROPHONE_INDEX: int | None = int(os.getenv("SMART_CANE_MICROPHONE_INDEX", "1"))

ALERT_VOICE_COOLDOWN_SEC: float = float(os.getenv("SMART_CANE_ALERT_COOLDOWN", "1.0"))

# LINE Messaging API 設定（可直接在 config.py 內寫死）
LINE_CHANNEL_ACCESS_TOKEN: str | None = os.getenv("SMART_CANE_LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET: str | None = os.getenv("SMART_CANE_LINE_CHANNEL_SECRET", "PASTE_YOUR_CHANNEL_SECRET_HERE")
LINE_TARGET_USER_ID: str | None = os.getenv("SMART_CANE_LINE_TARGET_USER_ID")
LINE_MESSAGING_API_URL: str = os.getenv("SMART_CANE_LINE_MESSAGING_API_URL", "https://api.line.me/v2/bot/message/push")

# logging
LOG_LEVEL: str = os.getenv("SMART_CANE_LOG_LEVEL", "INFO")
LOG_DIR: Path = Path(os.getenv("SMART_CANE_LOG_DIR", "./logs"))
LOG_FILE_NAME: str = os.getenv("SMART_CANE_LOG_FILE", "smart_cane.log")

# bundle
BUNDLE_DEFAULT_OUTPUT: str = os.getenv("SMART_CANE_BUNDLE_OUTPUT", "smart_cane_bundle.txt")
BUNDLE_IGNORE_DIRS: list[str] = [".git", "__pycache__", ".venv", "logs", "tmp"]

DATA_DIR: Path = Path(os.getenv("SMART_CANE_DATA_DIR", "./data"))
IMG_DIR: Path = DATA_DIR / "img"
ANALYZE_DIR: Path = DATA_DIR / "analyze"
