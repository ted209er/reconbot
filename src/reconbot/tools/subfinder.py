"""Lightweight wrapper for the subfinder CLI."""

from __future__ import annotations

import logging

from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "subfinder"


def find_subdomains(
    domain: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Run subfinder for a domain and return sorted unique subdomains."""
    result = run_command(
        "subfinder",
        [binary, "-silent", "-d", domain],
        timeout=timeout,
    )
    if not result.success:
        LOGGER.warning("subfinder failed for %s with code %s", domain, result.return_code)
        return []

    return parse_subdomains(result.output, domain)


def parse_subdomains(output: str, domain: str) -> list[str]:
    """Parse subfinder stdout into a sorted unique subdomain list."""
    normalized_domain = _normalize_domain(domain)
    subdomains = {
        candidate
        for line in output.splitlines()
        if (candidate := _normalize_domain(line))
        and candidate != normalized_domain
        and candidate.endswith(f".{normalized_domain}")
    }
    return sorted(subdomains)


def _normalize_domain(value: str) -> str:
    """Normalize a domain-like value from tool output."""
    return value.strip().lower().rstrip(".")
