"""Metric utilities for OCR evaluation."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Iterable, List, Sequence


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str, *, lowercase: bool = True) -> str:
    """Normalize text before metric computation.

    By default the function lowercases and collapses whitespace. This mirrors
    common OCR evaluation setups and reduces sensitivity to formatting.
    """

    normalized = unicodedata.normalize("NFKC", text)
    if lowercase:
        normalized = normalized.lower()
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def _levenshtein_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    """Compute Levenshtein distance between two sequences."""

    if reference == hypothesis:
        return 0
    if not reference:
        return len(hypothesis)
    if not hypothesis:
        return len(reference)

    previous_row = list(range(len(hypothesis) + 1))
    for ref_item in reference:
        current_row = [previous_row[0] + 1]
        for j, hyp_item in enumerate(hypothesis, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            replace_cost = previous_row[j - 1] + (0 if ref_item == hyp_item else 1)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


def _to_char_sequence(text: str) -> List[str]:
    return list(text)


def _to_word_sequence(text: str) -> List[str]:
    return normalize_text(text).split()


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Compute character error rate (CER)."""

    ref_chars = _to_char_sequence(normalize_text(reference))
    hyp_chars = _to_char_sequence(normalize_text(hypothesis))
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0
    distance = _levenshtein_distance(ref_chars, hyp_chars)
    return distance / len(ref_chars)


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute word error rate (WER)."""

    ref_tokens = _to_word_sequence(reference)
    hyp_tokens = _to_word_sequence(hypothesis)
    if not ref_tokens:
        return 0.0 if not hyp_tokens else 1.0
    distance = _levenshtein_distance(ref_tokens, hyp_tokens)
    return distance / len(ref_tokens)


def token_precision_recall_f1(reference: str, hypothesis: str) -> tuple[float, float, float]:
    """Compute token-level precision, recall and F1 using bag-of-words counts."""

    ref_tokens = _to_word_sequence(reference)
    hyp_tokens = _to_word_sequence(hypothesis)

    ref_counter = Counter(ref_tokens)
    hyp_counter = Counter(hyp_tokens)

    overlap = sum((ref_counter & hyp_counter).values())
    ref_total = sum(ref_counter.values())
    hyp_total = sum(hyp_counter.values())

    precision = overlap / hyp_total if hyp_total else 0.0
    recall = overlap / ref_total if ref_total else 0.0
    if precision + recall == 0.0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def exact_match(reference: str, hypothesis: str) -> float:
    """Return 1.0 if reference exactly matches hypothesis after normalization."""

    return 1.0 if normalize_text(reference) == normalize_text(hypothesis) else 0.0


def compute_metrics(reference: str, hypothesis: str) -> dict:
    """Compute a standard set of OCR metrics."""

    cer = character_error_rate(reference, hypothesis)
    wer = word_error_rate(reference, hypothesis)
    precision, recall, f1 = token_precision_recall_f1(reference, hypothesis)
    em = exact_match(reference, hypothesis)
    return {
        "character_error_rate": cer,
        "word_error_rate": wer,
        "token_precision": precision,
        "token_recall": recall,
        "token_f1": f1,
        "exact_match": em,
    }


def aggregate_confidences(confidences: Iterable[float | None]) -> float | None:
    """Compute the average of a collection of confidences ignoring ``None``."""

    filtered = [c for c in confidences if c is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return math.nan
    return sum(values) / len(values)
