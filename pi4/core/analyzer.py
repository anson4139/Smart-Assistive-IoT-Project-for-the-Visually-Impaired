from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from pi4.core.config import ANALYZE_DIR

ANALYZE_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_component(value: str, default: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_.-]+", "_", value)
    cleaned = cleaned.strip("_.-")
    return cleaned or default


def log_analysis(
    photo_name: Optional[str],
    response_payload: Any,
    description: str,
    tags: Iterable[str] | None = None,
) -> Path:
    """Persist the latest analysis result as a structured JSON text file."""
    base = photo_name or "img_unknown"
    descr_component = _sanitize_component(description, "analysis")[:64]
    sanitized_tags: list[str] = []
    if tags:
        for tag in tags:
            cleaned_tag = _sanitize_component(tag, "")
            if cleaned_tag:
                sanitized_tags.append(cleaned_tag)
    tag_component = ""
    if sanitized_tags:
        tag_component = "_" + "_".join(sanitized_tags)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{base}_{descr_component}{tag_component}_{timestamp}.txt"
    target = ANALYZE_DIR / filename
    payload = {
        "photo": photo_name,
        "description": description,
        "response": response_payload,
        "ts": datetime.now().isoformat(),
        "tags": sanitized_tags,
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
