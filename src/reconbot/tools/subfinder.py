"""Lightweight wrapper for the subfinder CLI."""

from __future__ import annotations

import logging

from reconbot.collection_status import CollectionStatus, status_from_result
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "subfinder"


def find_subdomains(
    domain: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    collection_statuses: list[CollectionStatus] | None = None,
) -> list[str]:
    """Run subfinder for a domain and return sorted unique subdomains."""
    result = run_command(
        "subfinder",
        [binary, "-silent", "-d", domain],
        timeout=timeout,
    )
    subdomains = parse_subdomains(result.output, domain) if result.success else []
    if collection_statuses is not None:
        collection_statuses.append(
            status_from_result(
                source="subfinder",
                target=domain,
                result=result,
                result_count=len(subdomains),
            )
        )
    if not result.success:
        LOGGER.warning("subfinder failed for %s with code %s", domain, result.return_code)
        return []

    return subdomains


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
