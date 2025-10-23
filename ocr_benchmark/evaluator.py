"""Benchmark orchestration logic."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence

from .data_loader import DocumentSample
from .metrics import aggregate_confidences, compute_metrics, safe_mean
from .models.base import BaseExtractor


@dataclass
class SampleEvaluation:
    sample_id: str
    prediction: str
    ground_truth: str
    metrics: Dict[str, float]
    confidence: float | None
    latency_seconds: float
    extractor_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodEvaluation:
    method_name: str
    aggregated_metrics: Dict[str, float]
    average_confidence: float | None
    average_latency_seconds: float
    samples: List[SampleEvaluation] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    dataset_size: int
    methods: Dict[str, MethodEvaluation]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_size": self.dataset_size,
            "methods": {
                name: {
                    "aggregated_metrics": method.aggregated_metrics,
                    "average_confidence": method.average_confidence,
                    "average_latency_seconds": method.average_latency_seconds,
                    "samples": [
                        {
                            "sample_id": sample.sample_id,
                            "prediction": sample.prediction,
                            "ground_truth": sample.ground_truth,
                            "metrics": sample.metrics,
                            "confidence": sample.confidence,
                            "latency_seconds": sample.latency_seconds,
                            "extractor_metadata": sample.extractor_metadata,
                        }
                        for sample in method.samples
                    ],
                }
                for name, method in self.methods.items()
            },
            "metadata": self.metadata,
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class BenchmarkRunner:
    """Runs OCR extractors on a dataset and aggregates metrics."""

    def __init__(self, samples: Sequence[DocumentSample]) -> None:
        self.samples = list(samples)

    def evaluate_method(self, extractor: BaseExtractor) -> MethodEvaluation:
        sample_reports: List[SampleEvaluation] = []
        metric_accumulator: Dict[str, List[float]] = {}
        confidences: List[float | None] = []
        latencies: List[float] = []

        for sample in self.samples:
            start = time.perf_counter()
            result = extractor.run(sample)
            latency = time.perf_counter() - start

            metrics = compute_metrics(sample.ground_truth, result.text)
            for key, value in metrics.items():
                metric_accumulator.setdefault(key, []).append(value)

            sample_reports.append(
                SampleEvaluation(
                    sample_id=sample.id,
                    prediction=result.text,
                    ground_truth=sample.ground_truth,
                    metrics=metrics,
                    confidence=result.confidence,
                    latency_seconds=latency,
                    extractor_metadata=result.metadata,
                )
            )
            confidences.append(result.confidence)
            latencies.append(latency)

        aggregated = {metric: safe_mean(values) for metric, values in metric_accumulator.items()}
        avg_confidence = aggregate_confidences(confidences)
        avg_latency = safe_mean(latencies)

        return MethodEvaluation(
            method_name=extractor.name,
            aggregated_metrics=aggregated,
            average_confidence=avg_confidence,
            average_latency_seconds=avg_latency,
            samples=sample_reports,
        )

    def run(self, extractors: Iterable[BaseExtractor]) -> BenchmarkReport:
        methods: Dict[str, MethodEvaluation] = {}
        for extractor in extractors:
            methods[extractor.name] = self.evaluate_method(extractor)
            extractor.cleanup()

        metadata = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return BenchmarkReport(
            dataset_size=len(self.samples),
            methods=methods,
            metadata=metadata,
        )
