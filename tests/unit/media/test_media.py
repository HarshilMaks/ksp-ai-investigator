from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from src.adapters.onnx import ModelUnavailableError, OptionalModel
from src.services.ocr import OCRService
from src.services.voice import TranslationService, VoiceService


class MediaBoundaryTests(unittest.TestCase):
    def test_missing_models_degrade_without_network_or_asset_download(self) -> None:
        translation = TranslationService().translate("Synthetic Ramesh report", source_language="en", target_language="kn", proper_nouns=("Ramesh",))
        transcription = VoiceService().transcribe(b"synthetic-audio")
        synthesis = VoiceService().synthesize("Synthetic report")
        ocr = OCRService().extract(b"synthetic-document")
        self.assertTrue(translation.degraded)
        self.assertEqual(("Ramesh",), translation.preserved_entities)
        self.assertTrue(transcription.degraded)
        self.assertTrue(synthesis.degraded)
        self.assertTrue(ocr.degraded)

    def test_optional_model_loads_only_an_injected_local_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "model.onnx"
            model = OptionalModel("test", asset)
            with self.assertRaises(ModelUnavailableError):
                model.load()
            asset.write_bytes(b"synthetic")
            loaded = OptionalModel("test", asset, loader=lambda path: path.read_bytes())
            self.assertEqual(b"synthetic", loaded.load())
            self.assertTrue(loaded.status.available)


if __name__ == "__main__":
    unittest.main()
