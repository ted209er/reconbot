"""Lightweight wrapper for the gau CLI."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from reconbot.utils.normalize import http_urls, non_empty_strings
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "gau"


def find_urls(
    targets: str | Sequence[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Run gau for a domain or live hosts and return sorted unique HTTP/HTTPS URLs."""
    urls: set[str] = set()
    for target in _normalize_targets(targets):
        result = run_command(
            "gau",
            [binary, target],
            timeout=timeout,
        )
        if not result.success:
            LOGGER.warning("gau failed for %s with code %s", target, result.return_code)
            continue

        urls.update(parse_urls(result.output))

    return sorted(urls)


def parse_urls(output: str) -> list[str]:
    """Parse gau stdout into HTTP/HTTPS URLs."""
    return http_urls(output.splitlines())


def _normalize_targets(targets: str | Sequence[str]) -> list[str]:
    """Normalize domain or host inputs into a list of non-empty target strings."""
    if isinstance(targets, str):
        values = [targets]
    else:
        values = list(targets)
    return non_empty_strings(values)
