"""Command line interface for running OCR benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .data_loader import limit_samples, load_manifest
from .evaluator import BenchmarkRunner
from .models import PlainTextExtractor, TextractExtractor
from .reporting import as_markdown_table, format_report


def _build_extractor(name: str, args: argparse.Namespace):
    name = name.lower()
    if name == "plaintext":
        return PlainTextExtractor()
    if name == "textract":
        return TextractExtractor(
            region_name=args.textract_region,
            api_mode=args.textract_mode,
            feature_types=args.textract_feature_types,
            profile_name=args.textract_profile,
        )
    raise ValueError(f"Unknown extractor '{name}'. Available: plaintext, textract")


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCR benchmark suite")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/omnidoc_sample/manifest.jsonl"),
        help="Path to the OmniDocBench-style sample manifest (JSONL)",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["plaintext"],
        help="List of extractors to benchmark (plaintext, textract, ...)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit evaluation to the first N samples",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Write detailed benchmark report to this JSON file",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Also print a markdown table summarizing results",
    )
    parser.add_argument(
        "--textract-region",
        default=None,
        help="AWS region to use for Textract (falls back to environment configuration)",
    )
    parser.add_argument(
        "--textract-profile",
        default=None,
        help="Name of the AWS shared credentials profile to use for Textract",
    )
    parser.add_argument(
        "--textract-mode",
        default="detect_document_text",
        choices=["detect_document_text", "analyze_document"],
        help="Textract API mode",
    )
    parser.add_argument(
        "--textract-feature-types",
        nargs="*",
        default=None,
        help="Feature types for Textract analyze_document",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    samples = load_manifest(args.manifest)
    if args.limit is not None:
        samples = limit_samples(samples, args.limit)

    runner = BenchmarkRunner(samples)
    extractors = [_build_extractor(name, args) for name in args.methods]
    report = runner.run(extractors)

    if args.output_json:
        args.output_json.write_text(report.to_json(), encoding="utf-8")

    print(format_report(report))
    if args.markdown:
        print("\n" + as_markdown_table(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
