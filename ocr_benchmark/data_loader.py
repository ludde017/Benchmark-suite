"""Utilities for loading OCR benchmark datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


@dataclass
class DocumentSample:
    """Represents a single document (page) to evaluate."""

    id: str
    source: Path
    ground_truth: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def load_bytes(self) -> bytes:
        """Load the raw bytes for the source file.

        This is primarily used by OCR extractors that need access to the
        original binary representation such as AWS Textract.
        """

        return self.source.read_bytes()

    def load_text(self, encoding: str = "utf-8") -> str:
        """Load the source as text if the file is textual."""

        return self.source.read_text(encoding=encoding)

    @property
    def split(self) -> str:
        return str(self.metadata.get("split", "unknown"))


def load_manifest(manifest_path: Path | str) -> List[DocumentSample]:
    """Load dataset entries from a JSON Lines manifest.

    Each line in the manifest should contain a JSON object with at least the
    following keys:

    - ``id``: unique identifier for the sample.
    - ``source``: path to the document/image relative to the manifest.
    - either ``ground_truth`` containing the reference transcription directly
      or ``ground_truth_path`` pointing to a UTF-8 encoded text file relative to
      the manifest location.

    Any remaining keys are stored under ``metadata``.
    """

    manifest = Path(manifest_path)
    if not manifest.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest}")

    samples: List[DocumentSample] = []
    with manifest.open("r", encoding="utf-8") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_no} of {manifest}: {exc}"
                ) from exc

            try:
                sample_id = record["id"]
                source_path = manifest.parent / record["source"]
            except KeyError as exc:
                raise KeyError(
                    f"Missing required key {exc} on line {line_no} of {manifest}"
                ) from exc

            if "ground_truth" in record:
                ground_truth = record["ground_truth"]
            elif "ground_truth_path" in record:
                gt_path = manifest.parent / record["ground_truth_path"]
                if not gt_path.exists():
                    raise FileNotFoundError(
                        f"Ground truth file not found for {sample_id}: {gt_path}"
                    )
                ground_truth = gt_path.read_text(encoding="utf-8")
            else:
                raise KeyError(
                    f"Either 'ground_truth' or 'ground_truth_path' must be provided "
                    f"for sample {sample_id}"
                )

            metadata: Dict[str, Any] = {
                key: value
                for key, value in record.items()
                if key not in {"id", "source", "ground_truth", "ground_truth_path"}
            }
            samples.append(
                DocumentSample(
                    id=str(sample_id),
                    source=source_path,
                    ground_truth=str(ground_truth),
                    metadata=metadata,
                )
            )

    if not samples:
        raise ValueError(f"Manifest {manifest} did not yield any samples")

    return samples


def limit_samples(samples: Sequence[DocumentSample], limit: int | None) -> List[DocumentSample]:
    """Return at most ``limit`` samples preserving order."""

    if limit is None or limit >= len(samples):
        return list(samples)
    return list(samples)[:limit]


def iter_batches(samples: Sequence[DocumentSample], batch_size: int) -> Iterable[List[DocumentSample]]:
    """Yield batches of samples of size ``batch_size``."""

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    batch: List[DocumentSample] = []
    for sample in samples:
        batch.append(sample)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
