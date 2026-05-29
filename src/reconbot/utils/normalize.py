"""Small deterministic normalization helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlparse


def strip_value(value: str) -> str:
    """Strip surrounding whitespace from a string."""
    return value.strip()


def non_empty_strings(values: Iterable[str]) -> list[str]:
    """Strip values and return only non-empty strings."""
    return [stripped for value in values if (stripped := strip_value(value))]


def dedupe_sorted(values: Iterable[str]) -> list[str]:
    """Return sorted unique non-empty strings."""
    return sorted(set(non_empty_strings(values)))


def normalize_domain(value: str) -> str:
    """Normalize a domain-like value."""
    return strip_value(value).lower().rstrip(".")


def normalize_url(value: str) -> str:
    """Normalize a URL-like value for lightweight output handling."""
    return strip_value(value).lower().rstrip("/")


def http_urls(values: Iterable[str]) -> list[str]:
    """Return sorted unique HTTP/HTTPS URLs."""
    return dedupe_sorted(
        normalized
        for value in values
        if (normalized := normalize_url(value))
        and (normalized.startswith("http://") or normalized.startswith("https://"))
    )


def hostnames_from_urls(urls: Iterable[str]) -> list[str]:
    """Extract sorted unique hostnames from URLs."""
    return dedupe_sorted(parsed.netloc for url in urls if (parsed := urlparse(url)).netloc)


def safe_filename(value: str, *, default: str = "report") -> str:
    """Return a simple filesystem-safe filename stem."""
    normalized = normalize_domain(value)
    safe_value = re.sub(r"[^a-z0-9._-]+", "-", normalized).strip("-._")
    return safe_value or default
