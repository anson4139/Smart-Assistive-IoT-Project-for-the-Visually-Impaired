from __future__ import annotations

import argparse
import time
from statistics import mean
from typing import Iterable

from pi4.core.config import CAMERA_DEVICE_INDEX
from pi4.core.logger import get_logger
from pi4.safety.vision import camera_capture, ncs_inference

LOGGER = get_logger("calibrate_detection")


def _capture_frames(sample_count: int, interval: float) -> list:
    frames = []
    for idx in range(sample_count):
        frame = camera_capture.get_frame()
        frames.append(frame)
        LOGGER.info("Captured frame %d/%d", idx + 1, sample_count)
        time.sleep(interval)
    return frames


def _evaluate_threshold(frames: Iterable, thresholds: Iterable[float]) -> list[dict]:
    results = []
    for threshold in thresholds:
        previous_confidence = ncs_inference.OPENVINO_CONFIDENCE
        try:
            ncs_inference.OPENVINO_CONFIDENCE = threshold
            detection_flags = []
            confidences: list[float] = []
            total_detections = 0
            for frame in frames:
                detections = ncs_inference.detect_objects(frame)
                detection_flags.append(bool(detections))
                total_detections += len(detections)
                confidences.extend(det.confidence for det in detections)
            detection_ratio = sum(detection_flags) / len(detection_flags)
            average_confidence = mean(confidences) if confidences else 0.0
            average_detections = total_detections / len(frames)
            results.append(
                {
                    "threshold": threshold,
                    "ratio": detection_ratio,
                    "avg_confidence": average_confidence,
                    "avg_detections": average_detections,
                }
            )
        finally:
            ncs_inference.OPENVINO_CONFIDENCE = previous_confidence
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate OpenVINO detection confidence by sampling camera frames."
    )
    parser.add_argument(
        "--samples",
        "-s",
        type=int,
        default=20,
        help="Number of frames to sample at the current camera configuration.",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=0.5,
        help="Seconds between sampled frames.",
    )
    parser.add_argument(
        "--thresholds",
        "-t",
        nargs="+",
        type=float,
        default=[0.4, 0.3, 0.25, 0.2],
        help="List of confidence thresholds to evaluate.",
    )
    args = parser.parse_args()

    print("Starting calibration for camera device", CAMERA_DEVICE_INDEX)
    frames = _capture_frames(args.samples, args.interval)
    print("Evaluating thresholds", args.thresholds)
    results = _evaluate_threshold(frames, args.thresholds)
    headers = "threshold | detection ratio | avg detections | avg confidence"
    print(headers)
    print("---")
    for entry in results:
        print(
            f"{entry['threshold']:.2f} | {entry['ratio']:.2%} | {entry['avg_detections']:.2f} | {entry['avg_confidence']:.2f}"
        )
    print("Calibration complete. Choose the threshold that keeps detection ratio >50% without too many false positives.")


if __name__ == "__main__":
    main()
