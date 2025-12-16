from __future__ import annotations

from typing import Iterable

import requests

from pi4.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED,
    OLLAMA_MODEL,
    OLLAMA_REWRITE_TIMEOUT_SEC,
)
from pi4.core.event_schema import Event
from pi4.core.logger import get_logger

LOGGER = get_logger("understanding_ollama_client")


_AVAILABLE_OLLAMA_MODELS: set[str] | None = None


def _get_available_models() -> set[str] | None:
    global _AVAILABLE_OLLAMA_MODELS
    if _AVAILABLE_OLLAMA_MODELS is not None:
        return _AVAILABLE_OLLAMA_MODELS
    try:
        response = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/v1/models", timeout=3.0)
        response.raise_for_status()
        payload = response.json()
        models = set()
        candidates: list[object] = []
        if isinstance(payload, dict):
            candidates = payload.get("models") or payload.get("data") or []
        elif isinstance(payload, list):
            candidates = payload
        for entry in candidates:
            if isinstance(entry, str):
                models.add(entry)
            elif isinstance(entry, dict):
                name = (
                    entry.get("name")
                    or entry.get("model")
                    or entry.get("model_name")
                    or entry.get("id")
                )
                if name:
                    models.add(name)
        _AVAILABLE_OLLAMA_MODELS = models
        return models
    except requests.RequestException:
        _AVAILABLE_OLLAMA_MODELS = None
        return None
    except ValueError:
        _AVAILABLE_OLLAMA_MODELS = None
        return None


def _is_model_available() -> bool:
    models = _get_available_models()
    if models is None:
        return True
    if OLLAMA_MODEL in models:
        return True
    LOGGER.warning(
        "Ollama model %s not listed (available: %s)",
        OLLAMA_MODEL,
        ", ".join(sorted(models)),
    )
    return False


def summarize_events(events: Iterable[Event]) -> str:
    """Summarize danger events into a concise Chinese message."""
    if not OLLAMA_ENABLED or not _is_model_available():
        return ""
    items: list[str] = []
    for event in events:
        items.append(f"{event.type}@{event.source} ({event.severity})")
    if not items:
        return ""
    meta = f"{OLLAMA_BASE_URL}/{OLLAMA_MODEL}"
    return f"Ollama summary [{meta}]: " + "；".join(items)


def rewrite_voice_text(events: Iterable[Event], original_text: str) -> tuple[str, bool]:
    """Use Ollama to rewrite safety text into a friendly voice copy."""
    if not OLLAMA_ENABLED or not _is_model_available():
        return original_text, False
    prompt_events: list[str] = []
    for event in events:
        distance = (
            f"{event.distance_m:.1f} 公尺"
            if event.distance_m is not None
            else "距離未知"
        )
        direction = event.direction or "方向未知"
        label = event.object_label or event.type.split(".")[-1]
        prompt_events.append(
            f"事件：{label}，{distance}，{direction}，等級 {event.severity}。"
        )
    if not prompt_events:
        return original_text, False
    system_prompt = (
        "你是溫柔貼心的導盲志工。"
        "請用溫暖、關懷的語氣，像朋友一樣提醒使用者注意前方的狀況。"
        "規則：1. 不要使用任何 Markdown (如 **粗體**)。 2. 不要解釋原因。 3. 不要列點。 4. 直接輸出要唸出的句子。"
        "例如：『小心喔，前方三公尺有下樓階梯，請慢慢走。』"
    )
    user_prompt = (
        f"原始播報：{original_text}\n" + "事件細節：" + "；".join(prompt_events)
    )
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    try:
        response = requests.post(url, json=payload, timeout=OLLAMA_REWRITE_TIMEOUT_SEC)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if choices:
            message = choices[0].get("message", {}).get("content") or choices[0].get("text")
            if message:
                return message.strip(), True
    except requests.RequestException as exc:
        LOGGER.warning("Ollama rewrite failed: %s", exc)
    except ValueError:
        LOGGER.warning("Ollama rewrite response not JSON")
    return original_text, False
