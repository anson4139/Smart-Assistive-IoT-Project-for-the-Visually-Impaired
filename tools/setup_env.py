from __future__ import annotations

from pathlib import Path
from typing import Iterable

SAMPLE = Path(__file__).resolve().parent.parent / ".env.sample"
TARGET = Path(__file__).resolve().parent.parent / ".env"


def _prompt(lines: Iterable[str]) -> list[str]:
    result: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            result.append(raw)
            continue
        if "=" not in raw:
            result.append(raw)
            continue
        key, val = raw.split("=", 1)
        key = key.strip()
        val = val.strip()
        new = input(f"{key} [{val}]: ") or val
        result.append(f"{key}={new}")
    return result


def main() -> None:
    if not SAMPLE.exists():
        raise FileNotFoundError(".env.sample is missing")
    lines = SAMPLE.read_text(encoding="utf-8").splitlines()
    filled = _prompt(lines)
    TARGET.write_text("\n".join(filled) + "\n", encoding="utf-8")
    print(f"Written {TARGET}")


if __name__ == "__main__":
    main()
