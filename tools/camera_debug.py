from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
import time

from pi4.safety.vision import camera_capture, vision_safety


def _format_event(event) -> str:
    parts = [event.severity, event.object_label or event.type]
    if event.distance_m is not None:
        parts.append(f"{event.distance_m:.2f} m")
    if event.direction is not None:
        parts.append(f"{event.direction}")
    return " | ".join(str(part) for part in parts)


def main() -> None:
    parser = ArgumentParser(description="Quickly verify camera + OpenVINO detection for a given camera index.")
    parser.add_argument("--interval", "-i", type=float, default=0.5, help="Seconds between captures")
    parser.add_argument("--count", "-c", type=int, default=0, help="Limit number of loops (0 for infinite)")
    args = parser.parse_args()

    loop = 0
    try:
        print("Camera debug loop running (Ctrl+C to stop). Set SMART_CANE_CAMERA_INDEX before invocation.")
        while args.count <= 0 or loop < args.count:
            frame = camera_capture.get_frame()
            source = camera_capture.last_frame_source()
            events = vision_safety.process_frame(frame)
            now = datetime.now().strftime("%H:%M:%S")
            shape = getattr(frame, "shape", None)
            dims = f"{shape[1]}x{shape[0]}" if shape else "unknown"
            print(f"[{now}] source={source} shape={dims} detections={len(events)}")
            for idx, event in enumerate(events, start=1):
                print(f"  {idx}. {_format_event(event)}")
            loop += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Camera debug loop stopped.")


if __name__ == "__main__":
    main()
