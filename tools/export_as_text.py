from __future__ import annotations

import argparse
import json
from pathlib import Path

from pi4.core.config import BUNDLE_DEFAULT_OUTPUT, BUNDLE_IGNORE_DIRS, PLATFORM


def export_as_text(root: Path, output: Path, ignore_dirs: list[str]) -> None:
    root = root.resolve()
    with output.open("w", encoding="utf-8") as writer:
        for entry in sorted(root.rglob("*")):
            if entry.is_dir():
                continue
            if any(part in ignore_dirs for part in entry.parts):
                continue
            rel_path = entry.relative_to(root)
            data = {
                "path": str(rel_path).replace("\\", "/"),
                "mode": oct(entry.stat().st_mode & 0o777),
            }
            try:
                text = entry.read_text(encoding="utf-8")
                data["type"] = "text"
                data["content"] = text
            except UnicodeDecodeError:
                data["type"] = "binary"
                data["content"] = entry.read_bytes().decode("latin-1")
            writer.write(json.dumps(data, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export project as JSON lines text bundle.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Root directory to export.")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--platform",
        choices=("desktop", "pi4"),
        default=PLATFORM,
        help="Describe the host environment so we can pick OS-friendly defaults.",
    )
    args = parser.parse_args()
    platform = args.platform
    output = args.output or _get_default_output(platform)
    print(f"Exporting bundle for {platform} to {output}")
    export_as_text(args.root, output, BUNDLE_IGNORE_DIRS)


def _get_default_output(platform: str) -> Path:
    base = Path("/home/pi") if platform == "pi4" else Path.cwd()
    if platform == "pi4" and not base.exists():
        base = Path.cwd()
    return (base / BUNDLE_DEFAULT_OUTPUT).resolve()


if __name__ == "__main__":
    main()
