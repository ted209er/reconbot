"""Lightweight wrapper for the assetfinder CLI."""

from __future__ import annotations

import logging

from reconbot.collection_status import CollectionStatus, status_from_result
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
    collection_statuses: list[CollectionStatus] | None = None,
) -> list[str]:
    """Run assetfinder for a domain and return sorted unique subdomains."""
    result = run_command(
        "assetfinder",
        [binary, "--subs-only", domain],
        timeout=timeout,
    )
    subdomains = parse_subdomains(result.output, domain) if result.success else []
    if collection_statuses is not None:
        collection_statuses.append(
            status_from_result(
                source="assetfinder",
                target=domain,
                result=result,
                result_count=len(subdomains),
            )
        )
    if not result.success:
        LOGGER.warning("assetfinder failed for %s with code %s", domain, result.return_code)
        return []

    return subdomains
