"""Extractor that reads plain-text files (useful for baselines/tests)."""

from __future__ import annotations

from ..data_loader import DocumentSample
from .base import BaseExtractor, OcrResult


class PlainTextExtractor(BaseExtractor):
    """Simple extractor that reads text files directly."""

    def __init__(self, encoding: str = "utf-8", name: str | None = None) -> None:
        super().__init__(name or "plaintext")
        self.encoding = encoding

    def run(self, sample: DocumentSample) -> OcrResult:
        text = sample.load_text(self.encoding)
        return OcrResult(text=text, confidence=1.0, metadata={"strategy": "file-read"})
