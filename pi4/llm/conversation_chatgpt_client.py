from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from pi4.core.config import (OPENAI_API_KEY, OPENAI_ENABLED, OPENAI_MODEL,
                             USE_CONVERSATION_LAYER)
from pi4.core.event_schema import Event


@dataclass
class ConversationContext:
    camera_events: List[Event]
    cane_events: List[Event]
    position: str
    time: datetime


def answer_question(ctx: ConversationContext, user_query: str) -> str:
    """Generate a polite Chinese response based on the context and query."""
    if not OPENAI_ENABLED or not USE_CONVERSATION_LAYER:
        return "Conversation layer已停用，請改用 Safety simulation。"
    if not OPENAI_API_KEY:
        raise ValueError("缺少 OPENAI_API_KEY，ChatGPT 無法呼叫")
    lines = []
    if ctx.camera_events:
        lines.append(f"視覺偵測到 {len(ctx.camera_events)} 個事件")
    if ctx.cane_events:
        lines.append(f"拐杖偵測到 {len(ctx.cane_events)} 個事件")
    summary = "；".join(lines) if lines else "目前沒有特別的事件"
    return (
        "目前偵測到: "
        + summary
        + "。"
        + "請自行注意周遭情況，避免冒險前往。"
    )
