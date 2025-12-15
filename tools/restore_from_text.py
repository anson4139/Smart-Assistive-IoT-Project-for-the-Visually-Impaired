from __future__ import annotations

import argparse
import json
from pathlib import Path


def restore_from_text(source: Path, target: Path, force: bool = False) -> None:
    target = target.resolve()
    if target.exists() and not force:
        raise FileExistsError(f"Target {target} already exists. Use --force to overwrite.")
    target.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8") as reader:
        for line in reader:
            entry = json.loads(line)
            rel_path = Path(entry["path"])
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            if entry["type"] == "text":
                dest.write_text(entry["content"], encoding="utf-8")
            else:
                dest.write_bytes(entry["content"].encode("latin-1"))
            if mode := entry.get("mode"):
                dest.chmod(int(mode, 8))


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore project from text bundle.")
    parser.add_argument("--input", type=Path, required=True, help="Bundle input file.")
    parser.add_argument("--target", type=Path, required=True, help="Target directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target.")
    args = parser.parse_args()
    restore_from_text(args.input, args.target, args.force)


if __name__ == "__main__":
    main()
