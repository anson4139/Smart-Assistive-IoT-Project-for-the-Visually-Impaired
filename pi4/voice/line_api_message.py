from __future__ import annotations

import requests
from typing import Mapping

from pi4.core.config import (
    LINE_CHANNEL_ACCESS_TOKEN,
    LINE_MESSAGING_API_URL,
    LINE_TARGET_USER_ID,
)
from pi4.core.logger import get_logger

LOGGER = get_logger("line_api_message")


class LineNotifier:
    def __init__(
        self,
        token: str | None = None,
        api_url: str = LINE_MESSAGING_API_URL,
        target_user_id: str | None = None,
    ) -> None:
        self._token = token or LINE_CHANNEL_ACCESS_TOKEN
        self._api_url = api_url
        self._target_user_id = target_user_id or LINE_TARGET_USER_ID

    def send(self, message: str, target_user_id: str | None = None) -> bool:
        user_id = target_user_id or self._target_user_id
        if not self._token or not user_id:
            LOGGER.warning(
                "LINE Messaging API missing token/user_id, drop message: %s", message
            )
            return False
        headers: Mapping[str, str] = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}
        try:
            response = requests.post(self._api_url, headers=headers, json=payload, timeout=3.0)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover
            LOGGER.exception("LINE Messaging API send failed: %s", exc)
            return False
        LOGGER.info("LINE Messaging API message sent to %s", user_id)
        return True
