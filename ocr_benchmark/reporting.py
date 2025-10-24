"""Helpers to pretty-print benchmark results."""

from __future__ import annotations

from .evaluator import BenchmarkReport, MethodEvaluation


def format_method_summary(method: MethodEvaluation) -> str:
    lines = [f"Method: {method.method_name}"]
    lines.append("  Aggregated metrics:")
    for metric_name, value in sorted(method.aggregated_metrics.items()):
        lines.append(f"    - {metric_name}: {value:.4f}")
    if method.average_confidence is not None:
        lines.append(f"  Average confidence: {method.average_confidence:.4f}")
    else:
        lines.append("  Average confidence: n/a")
    lines.append(f"  Average latency (s): {method.average_latency_seconds:.4f}")
    return "\n".join(lines)


def format_report(report: BenchmarkReport) -> str:
    lines = [
        f"Dataset size: {report.dataset_size}",
        f"Run timestamp: {report.metadata.get('timestamp', 'n/a')}",
    ]
    for method in report.methods.values():
        lines.append("")
        lines.append(format_method_summary(method))
    return "\n".join(lines)


def as_markdown_table(report: BenchmarkReport) -> str:
    """Return a markdown table summarizing aggregated metrics for each method."""

    if not report.methods:
        return "No methods evaluated"

    metric_names = set()
    for method in report.methods.values():
        metric_names.update(method.aggregated_metrics.keys())
    metric_names = sorted(metric_names)

    header = ["Method"] + [metric.replace("_", " ") for metric in metric_names] + [
        "Avg confidence",
        "Avg latency (s)",
    ]
    rows = [" | ".join(header), " | ".join(["---"] * len(header))]

    for method in report.methods.values():
        row = [method.method_name]
        for metric in metric_names:
            value = method.aggregated_metrics.get(metric)
            if value is None:
                row.append("n/a")
            else:
                row.append(f"{value:.4f}")
        if method.average_confidence is None:
            row.append("n/a")
        else:
            row.append(f"{method.average_confidence:.4f}")
        row.append(f"{method.average_latency_seconds:.4f}")
        rows.append(" | ".join(row))

    return "\n".join(rows)
