from __future__ import annotations

from typing import Any

import requests

from pi4.core.config import (OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_ENABLED,
                             OPENAI_MODEL, OLLAMA_BASE_URL, OLLAMA_ENABLED)


def run_ollama_smoke_test() -> bool:
    if not OLLAMA_ENABLED:
        print("Ollama disabled; skipping smoke test.")
        return False
    try:
        resp = requests.get(OLLAMA_BASE_URL, timeout=5)
        return resp.status_code == 200
    except requests.RequestException as exc:
        print(f"Ollama smoke test failed: {exc}")
        return False


def run_chatgpt_smoke_test() -> bool:
    if not OPENAI_ENABLED:
        print("ChatGPT disabled; skipping smoke test.")
        return False
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY 未設定。")
        return False
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": "請說一句安全提醒。"}],
        "temperature": 0.2,
    }
    try:
        resp = requests.post(
            f"{OPENAI_API_BASE}/chat/completions", json=payload, headers=headers, timeout=10
        )
        return resp.status_code == 200
    except requests.RequestException as exc:
        print(f"ChatGPT smoke test failed: {exc}")
        return False
