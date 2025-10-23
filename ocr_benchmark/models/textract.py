"""AWS Textract extractor implementation."""

from __future__ import annotations

from typing import Iterable, List, Optional

from ..data_loader import DocumentSample
from .base import BaseExtractor, OcrResult

try:  # pragma: no cover - optional dependency
    import boto3
except ImportError:  # pragma: no cover - boto3 not always installed
    boto3 = None  # type: ignore


class TextractExtractor(BaseExtractor):
    """Run OCR using AWS Textract."""

    def __init__(
        self,
        *,
        client=None,
        region_name: Optional[str] = None,
        api_mode: str = "detect_document_text",
        feature_types: Optional[List[str]] = None,
        profile_name: Optional[str] = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name or "textract")
        if client is not None:
            self._client = client
        else:
            if boto3 is None:
                raise ImportError(
                    "boto3 is required to use TextractExtractor. Install boto3 and "
                    "configure AWS credentials to enable this extractor."
                )
            session_kwargs = {}
            if profile_name:
                session_kwargs["profile_name"] = profile_name
            session = boto3.session.Session(**session_kwargs)
            self._client = session.client("textract", region_name=region_name)
        self.api_mode = api_mode
        self.feature_types = feature_types or ["TABLES", "FORMS"]

    def run(self, sample: DocumentSample) -> OcrResult:
        payload = {"Bytes": sample.load_bytes()}
        if self.api_mode == "detect_document_text":
            response = self._client.detect_document_text(Document=payload)
        elif self.api_mode == "analyze_document":
            response = self._client.analyze_document(
                Document=payload,
                FeatureTypes=self.feature_types,
            )
        else:  # pragma: no cover - defensive branch
            raise ValueError(f"Unsupported Textract api_mode: {self.api_mode}")

        text_lines, confidences = _collect_lines(response.get("Blocks", []))
        combined_text = "\n".join(text_lines)
        avg_conf = (
            sum(confidences) / len(confidences)
            if confidences
            else None
        )
        return OcrResult(
            text=combined_text,
            confidence=avg_conf,
            metadata={
                "textract_api_mode": self.api_mode,
                "textract_feature_types": self.feature_types,
            },
        )

    def cleanup(self) -> None:  # type: ignore[override]
        # boto3 clients do not require explicit cleanup but the hook exists for API parity.
        return None


def _collect_lines(blocks: Iterable[dict]) -> tuple[List[str], List[float]]:
    lines: List[str] = []
    confidences: List[float] = []
    for block in blocks:
        if block.get("BlockType") == "LINE":
            text = block.get("Text", "")
            if text:
                lines.append(text)
                conf = block.get("Confidence")
                if conf is not None:
                    confidences.append(float(conf) / 100.0)
    return lines, confidences
