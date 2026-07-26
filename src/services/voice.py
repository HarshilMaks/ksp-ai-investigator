"""Optional Kannada/English translation and voice model boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.adapters.onnx import ModelStatus, ModelUnavailableError, OptionalModel


@dataclass(frozen=True)
class TranslationResult:
    text: str
    source_language: str
    target_language: str
    degraded: bool
    preserved_entities: tuple[str, ...]
    model: str


class TranslationService:
    def __init__(self, model: OptionalModel | None = None) -> None:
        self.model = model or OptionalModel("IndicTrans2")

    def translate(self, text: str, *, source_language: str, target_language: str, proper_nouns: tuple[str, ...] = ()) -> TranslationResult:
        if not text.strip():
            raise ValueError("translation text is required")
        if source_language not in {"en", "kn"} or target_language not in {"en", "kn"}:
            raise ValueError("only English and Kannada translation is supported")
        if source_language == target_language:
            return TranslationResult(text, source_language, target_language, False, proper_nouns, "identity")
        try:
            model = self.model.load()
            translated = model.translate(text, source_language, target_language, proper_nouns)
            return TranslationResult(str(translated), source_language, target_language, False, proper_nouns, self.model.name)
        except (ModelUnavailableError, AttributeError):
            return TranslationResult(text, source_language, target_language, True, proper_nouns, "unavailable")


@dataclass(frozen=True)
class VoiceResult:
    text: str | None
    audio: bytes | None
    language: str
    degraded: bool
    model: str
    reason: str | None = None


class VoiceService:
    def __init__(self, *, transcriber: OptionalModel | None = None, synthesizer: OptionalModel | None = None) -> None:
        self.transcriber = transcriber or OptionalModel("Faster-Whisper")
        self.synthesizer = synthesizer or OptionalModel("Piper-Edge-TTS")

    def transcribe(self, audio: bytes, *, language: str = "en") -> VoiceResult:
        if not audio:
            raise ValueError("audio is required")
        try:
            model = self.transcriber.load()
            return VoiceResult(str(model.transcribe(audio, language)), None, language, False, self.transcriber.name)
        except (ModelUnavailableError, AttributeError):
            return VoiceResult(None, None, language, True, "unavailable", "voice model assets are absent")

    def synthesize(self, text: str, *, language: str = "en") -> VoiceResult:
        if not text.strip():
            raise ValueError("text is required")
        try:
            model = self.synthesizer.load()
            return VoiceResult(text, bytes(model.synthesize(text, language)), language, False, self.synthesizer.name)
        except (ModelUnavailableError, AttributeError):
            return VoiceResult(text, None, language, True, "unavailable", "voice model assets are absent")


__all__ = ["TranslationResult", "TranslationService", "VoiceResult", "VoiceService"]
