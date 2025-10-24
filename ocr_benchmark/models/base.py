"""Base classes for OCR extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

from ..data_loader import DocumentSample


@dataclass
class OcrResult:
    """Container for OCR outputs."""

    text: str
    confidence: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseExtractor(ABC):
    """Abstract base class for OCR extraction methods."""

    name: str

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__.lower()

    @abstractmethod
    def run(self, sample: DocumentSample) -> OcrResult:
        """Run OCR on the provided sample."""

    def cleanup(self) -> None:
        """Hook for subclasses to release resources."""

        return None
