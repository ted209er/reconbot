"""Lightweight wrapper for the assetfinder CLI."""

from __future__ import annotations

import logging

from reconbot.tools.subfinder import parse_subdomains
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "assetfinder"


def find_subdomains(
    domain: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Run assetfinder for a domain and return sorted unique subdomains."""
    result = run_command(
        "assetfinder",
        [binary, "--subs-only", domain],
        timeout=timeout,
    )
    if not result.success:
        LOGGER.warning("assetfinder failed for %s with code %s", domain, result.return_code)
        return []

    return parse_subdomains(result.output, domain)
