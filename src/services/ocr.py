"""Optional Tesseract-compatible OCR boundary with safe absence behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.adapters.onnx import ModelUnavailableError, OptionalModel


@dataclass(frozen=True)
class OCRResult:
    text: str
    language: str
    degraded: bool
    model: str
    confidence: float | None
    reason: str | None = None


class OCRService:
    def __init__(self, model: OptionalModel | None = None) -> None:
        self.model = model or OptionalModel("Tesseract")

    def extract(self, content: bytes, *, language: str = "eng+kan") -> OCRResult:
        if not content:
            raise ValueError("document content is required")
        try:
            engine = self.model.load()
            extracted = engine.extract(content, language)
            if isinstance(extracted, tuple):
                text, confidence = extracted
            else:
                text, confidence = extracted, None
            return OCRResult(str(text), language, False, self.model.name, confidence)
        except (ModelUnavailableError, AttributeError):
            return OCRResult("", language, True, "unavailable", None, "OCR model assets are absent")


__all__ = ["OCRResult", "OCRService"]
