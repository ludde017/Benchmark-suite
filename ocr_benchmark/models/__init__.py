"""OCR extractor implementations."""

from .base import BaseExtractor, OcrResult
from .plaintext import PlainTextExtractor
from .textract import TextractExtractor

__all__ = [
    "BaseExtractor",
    "OcrResult",
    "PlainTextExtractor",
    "TextractExtractor",
]
