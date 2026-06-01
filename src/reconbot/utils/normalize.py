"""Small deterministic normalization helpers."""

from __future__ import annotations

import re


def normalize_hostname(value: str) -> str:
    """Return a lowercase hostname without surrounding whitespace or a trailing dot."""
    return value.strip().lower().rstrip(".")


def safe_filename(value: str, default: str = "item") -> str:
    """Return a simple filesystem-safe filename stem."""
    normalized = value.strip().lower().replace("://", "-")
    safe_value = re.sub(r"[^a-z0-9-]+", "-", normalized).strip("-")
    return safe_value or default
