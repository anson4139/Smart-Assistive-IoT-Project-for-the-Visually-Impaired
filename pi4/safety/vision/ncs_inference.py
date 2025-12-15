from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from pi4.core.config import (OPENVINO_CONFIDENCE, OPENVINO_DEVICE,
                             OPENVINO_ENABLED, OPENVINO_LABELS,
                             OPENVINO_MODEL_BIN, OPENVINO_MODEL_XML)
from pi4.core.logger import get_logger

try:
    from openvino.runtime import Core
except ImportError:  # pragma: no cover
    Core = None

logger = get_logger("ncs_inference")


@dataclass
class DetectedObject:
    label: str
    bbox: Tuple[int, int, int, int]
    confidence: float


class _OpenVINOModel:
    def __init__(self) -> None:
        if not OPENVINO_ENABLED or Core is None or not OPENVINO_MODEL_XML:
            raise RuntimeError("OpenVINO not configured")
        core = Core()
        model = core.read_model(model=OPENVINO_MODEL_XML, weights=OPENVINO_MODEL_BIN)
        self.compiled = core.compile_model(model, device_name=OPENVINO_DEVICE)
        self.input_tensor = self.compiled.input(0)
        self.output_tensor = self.compiled.output(0)

    def infer(self, frame: "np.ndarray") -> np.ndarray:
        h, w = self.input_tensor.shape[2], self.input_tensor.shape[3]
        resized = cv2.resize(frame, (w, h))
        blob = resized.transpose(2, 0, 1)[None, ...]
        results = self.compiled([blob])[self.output_tensor]
        if results.ndim == 4:
            return results[0][0]
        return results.reshape(-1, 7)


_ov_model: Optional[_OpenVINOModel] = None


def _get_model() -> Optional[_OpenVINOModel]:
    global _ov_model
    if _ov_model is None:
        try:
            _ov_model = _OpenVINOModel()
        except RuntimeError as exc:
            logger.warning("OpenVINO not available: %s", exc)
            return None
    return _ov_model


def _label_for_class(class_id: int) -> str:
    return OPENVINO_LABELS.get(class_id, f"class_{class_id}")


def detect_objects(frame: "np.ndarray") -> List[DetectedObject]:
    """Return list of detected objects using OpenVINO model."""
    model = _get_model()
    if model is None:
        return []
    detections = []
    raw = model.infer(frame)
    height, width = frame.shape[:2]
    for det in raw:
        score = float(det[2])
        if score < OPENVINO_CONFIDENCE:
            continue
        class_id = int(det[1])
        x1 = int(max(0, det[3] * width))
        y1 = int(max(0, det[4] * height))
        x2 = int(min(width, det[5] * width))
        y2 = int(min(height, det[6] * height))
        detections.append(
            DetectedObject(
                label=_label_for_class(class_id),
                bbox=(x1, y1, x2, y2),
                confidence=score,
            )
        )
    return detections
