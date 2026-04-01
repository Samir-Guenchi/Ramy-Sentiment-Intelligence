"""
Dataset validation helpers for semicolon-delimited review files.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


ALLOWED_LABELS = {"positive", "negative", "neutral", "improvement", "question"}


def normalize_label(label: str) -> str:
    return (label or "").strip().lower()


def validate_row(parts: List[str]) -> Tuple[bool, Optional[Dict[str, str]], Optional[str]]:
    if not parts:
        return False, None, "empty_row"

    if len(parts) < 3:
        return False, None, "missing_columns"

    text = (parts[0] or "").strip()
    product = (parts[1] or "").strip()
    label = normalize_label(parts[2])

    if not text:
        return False, None, "empty_text"

    if len(text) < 2:
        return False, None, "short_text"

    if not label:
        return False, None, "empty_label"

    if label not in ALLOWED_LABELS:
        return False, None, "unknown_label"

    return True, {"text": text, "product": product, "label": label}, None
