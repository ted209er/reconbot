"""Small deterministic normalization helpers."""

from __future__ import annotations

import re


def safe_filename(value: str, default: str = "item") -> str:
    """Return a simple filesystem-safe filename stem."""
    normalized = value.strip().lower().replace("://", "-")
    safe_value = re.sub(r"[^a-z0-9._-]+", "-", normalized).strip("-._")
    return safe_value or default
