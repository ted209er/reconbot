"""Lightweight wrapper for the httpx CLI."""

from __future__ import annotations

import logging

from reconbot.utils.normalize import http_urls, strip_value
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "httpx"


def find_live_urls(
    subdomains: list[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Run httpx for subdomains and return sorted unique live HTTP/HTTPS URLs."""
    live_urls: set[str] = set()
    for subdomain in subdomains:
        target = strip_value(subdomain)
        if not target:
            continue

        result = run_command(
            "httpx",
            [binary, "-silent", "-u", target],
            timeout=timeout,
        )
        if not result.success:
            LOGGER.warning("httpx failed for %s with code %s", target, result.return_code)
            continue

        live_urls.update(parse_live_urls(result.output))

    return sorted(live_urls)


def parse_live_urls(output: str) -> list[str]:
    """Parse httpx stdout into HTTP/HTTPS URLs."""
    return http_urls(output.splitlines())
