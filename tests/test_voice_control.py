from __future__ import annotations

from typing import Callable

from pi4.voice.voice_control import VoiceCommandHandler


class DummyLineNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


def test_voice_commands_trigger_callbacks() -> None:
    start_calls: list[bool] = []
    stop_calls: list[bool] = []

    def start_safety() -> None:
        start_calls.append(True)

    def stop_safety() -> None:
        stop_calls.append(True)

    notifier = DummyLineNotifier()
    simulated_inputs = [
        "小A 開啟行人輔助",
        "嗨小A 關閉行人輔助",
        "我出發了",
        "我已經安全到達",
    ]

    handler = VoiceCommandHandler(
        start_safety=start_safety,
        stop_safety=stop_safety,
        line_notifier=notifier,
        simulated_inputs=simulated_inputs,
    )
    handler.start_listening()
    handler.join(timeout=2)
    handler.stop()

    assert start_calls == [True]
    assert stop_calls == [True]
    assert notifier.messages == [
        "使用者已出發，行人輔助開啟中。",
        "使用者已安全抵達，行人輔助關閉。",
    ]