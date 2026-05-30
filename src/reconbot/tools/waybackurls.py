"""Lightweight wrapper for the waybackurls CLI."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from reconbot.tools.gau import parse_urls
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "waybackurls"


def find_urls(
    targets: str | Sequence[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Run waybackurls for a domain or live hosts and return sorted unique URLs."""
    urls: set[str] = set()
    for target in _normalize_targets(targets):
        result = run_command(
            "waybackurls",
            [binary, target],
            timeout=timeout,
        )
        if not result.success:
            LOGGER.warning("waybackurls failed for %s with code %s", target, result.return_code)
            continue
        urls.update(parse_urls(result.output))
    return sorted(urls)


def _normalize_targets(targets: str | Sequence[str]) -> list[str]:
    """Normalize target inputs into non-empty strings."""
    if isinstance(targets, str):
        values = [targets]
    else:
        values = list(targets)
    return [value.strip() for value in values if value.strip()]
