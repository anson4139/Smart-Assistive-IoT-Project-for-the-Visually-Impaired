from __future__ import annotations

import glob
import sys
from pathlib import Path

import cv2

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pi4.safety.vision import ncs_inference


def main() -> int:
    image_dir = Path("data/img")
    files = sorted(image_dir.glob("*.jpg"))
    if not files:
        print("No saved images found in data/img", file=sys.stderr)
        return 1
    latest = files[-1]
    frame = cv2.imread(str(latest))
    if frame is None:
        print(f"Failed to read {latest}", file=sys.stderr)
        return 1
    detections = ncs_inference.detect_objects(frame)
    print(f"Running inference on {latest.name} ({frame.shape[1]}x{frame.shape[0]})")
    if not detections:
        print("No detections found.")
        return 0
    for idx, det in enumerate(detections, start=1):
        print(f"{idx}. {det.label} @ confidence={det.confidence:.2f}, bbox={det.bbox}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
