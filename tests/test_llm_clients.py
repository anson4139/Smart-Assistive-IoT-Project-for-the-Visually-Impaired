from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pi4.core.event_schema import Event
from pi4.llm import (conversation_chatgpt_client,
                     understanding_ollama_client)


def test_summarize_events_returns_message() -> None:
    events = [
        Event(
            event_id="evt-1",
            ts=datetime.now(timezone.utc),
            type="vision.person",
            source="camera",
            severity="mid",
        )
    ]
    summary = understanding_ollama_client.summarize_events(events)
    assert "vision.person" in summary


def test_rewrite_voice_text_returns_original_when_disabled(monkeypatch) -> None:
    monkeypatch.setattr(understanding_ollama_client, "OLLAMA_ENABLED", False)
    event = Event(
        event_id="evt-2",
        ts=datetime.now(timezone.utc),
        type="vision.person",
        source="camera",
        severity="high",
    )
    rewritten, used = understanding_ollama_client.rewrite_voice_text([event], "原始文字")
    assert rewritten == "原始文字"
    assert used is False


def test_rewrite_voice_text_calls_ollama(monkeypatch) -> None:
    monkeypatch.setattr(understanding_ollama_client, "OLLAMA_ENABLED", True)
    monkeypatch.setattr(understanding_ollama_client, "OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setattr(understanding_ollama_client, "OLLAMA_MODEL", "llama3.1:8b")

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, list[dict[str, dict[str, str]]]]:
            return {"choices": [{"message": {"content": "親民語句"}}]}

    monkeypatch.setattr(
        "pi4.llm.understanding_ollama_client.requests.post",
        lambda *args, **kwargs: DummyResponse(),
    )

    event = Event(
        event_id="evt-3",
        ts=datetime.now(timezone.utc),
        type="vision.person",
        source="camera",
        severity="high",
    )
    rewritten, used = understanding_ollama_client.rewrite_voice_text([event], "原始文字")
    assert rewritten == "親民語句"
    assert used is True


def test_answer_question_with_api_key(monkeypatch) -> None:
    monkeypatch.setattr(conversation_chatgpt_client, "OPENAI_API_KEY", "key")
    monkeypatch.setattr(conversation_chatgpt_client, "OPENAI_ENABLED", True)
    ctx = conversation_chatgpt_client.ConversationContext(
        camera_events=[],
        cane_events=[],
        position="前方",
        time=datetime.now(timezone.utc),
    )
    answer = conversation_chatgpt_client.answer_question(ctx, "現在安全嗎？")
    assert "一定安全" not in answer
    assert "完全沒問題" not in answer


def run_tests_unit() -> bool:
    return pytest.main([__file__]) == 0
