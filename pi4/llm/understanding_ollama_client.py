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



_ACTIVE_MODEL: str | None = None

def _is_model_available() -> bool:
    global _ACTIVE_MODEL
    # If we already selected a valid model, reuse it
    if _ACTIVE_MODEL:
        return True

    models = _get_available_models()
    if models is None:
        # Cannot reach Ollama, trust config or fail later
        return True
    
    # Check if configured model exists
    if OLLAMA_MODEL in models:
        _ACTIVE_MODEL = OLLAMA_MODEL
        return True
    
    # Fallback Strategy:
    # 1. Try to find any model with "gemma" in the name
    # 2. Try to find any model with "llama" in the name
    # 3. Pick the first available model
    
    logger_msg = f"Ollama model {OLLAMA_MODEL} not found."
    
    for candidate in models:
        if "gemma" in candidate.lower():
            _ACTIVE_MODEL = candidate
            LOGGER.warning(f"{logger_msg} Falling back to similar model: {_ACTIVE_MODEL}")
            return True
            
    for candidate in models:
        if "llama" in candidate.lower() or "gpt" in candidate.lower():
            _ACTIVE_MODEL = candidate
            LOGGER.warning(f"{logger_msg} Falling back to: {_ACTIVE_MODEL}")
            return True
            
    if models:
        _ACTIVE_MODEL = list(models)[0]
        LOGGER.warning(f"{logger_msg} Falling back to available model: {_ACTIVE_MODEL}")
        return True

    LOGGER.error(f"{logger_msg} No models available on server.")
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
    meta = f"{OLLAMA_BASE_URL}/{_ACTIVE_MODEL or OLLAMA_MODEL}"
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
        "model": _ACTIVE_MODEL or OLLAMA_MODEL,
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


def rewrite_caregiver_text(events: Iterable[Event], original_text: str) -> str:
    """Use Ollama to generate an objective safety report for caregivers."""
    if not OLLAMA_ENABLED or not _is_model_available():
        return f"[系統自動回報] {original_text} (AI 未連線)"

    prompt_events: list[str] = []
    for event in events:
        distance = (
            f"{event.distance_m:.1f} 公尺"
            if event.distance_m is not None
            else "距離未知"
        )
        label = event.object_label or event.type.split(".")[-1]
        prompt_events.append(
            f"物件：{label} | 距離：{distance} | 等級：{event.severity}"
        )

    if not prompt_events:
        return f"[系統自動回報] {original_text}"

    system_prompt = (
        "你是視障者的安全回報系統。"
        "請將收到的事件資訊整理成給『家屬/照護者』的LINE通知訊息。"
        "規則：1. 語氣要客觀、精確、專業。 2. 讓家屬清楚知道發生什麼危險，但不要過度恐慌。 3. 不要使用 Markdown。 4. 直接輸出訊息內容。"
        "格式範例：『【安全回報】使用者前方 2.5 公尺偵測到台階，系統已發出語音提醒。』"
    )
    
    user_prompt = (
        f"系統語音內容：{original_text}\n" + "感測器數據：" + "；".join(prompt_events)
    )

    payload = {
        "model": _ACTIVE_MODEL or OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,  # Lower temperature for more factual output
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
                return message.strip()
    except Exception as exc:
        LOGGER.warning("Ollama caregiver rewrite failed: %s", exc)
        
    # Fallback if AI fails
    return f"[系統自動回報] {original_text}"
