"""Lightweight wrapper for the gau CLI."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from reconbot.collection_status import CollectionStatus, status_from_result
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "gau"


def find_urls(
    targets: str | Sequence[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    collection_statuses: list[CollectionStatus] | None = None,
) -> list[str]:
    """Run gau for a domain or live hosts and return sorted unique HTTP/HTTPS URLs."""
    urls: set[str] = set()
    for target in _normalize_targets(targets):
        result = run_command(
            "gau",
            [binary, target],
            timeout=timeout,
        )
        parsed_urls = parse_urls(result.output) if result.success else []
        if collection_statuses is not None:
            collection_statuses.append(
                status_from_result(
                    source="gau",
                    target=target,
                    result=result,
                    result_count=len(parsed_urls),
                )
            )
        if not result.success:
            LOGGER.warning("gau failed for %s with code %s", target, result.return_code)
            continue

        urls.update(parsed_urls)

    return sorted(urls)


def parse_urls(output: str) -> list[str]:
    """Parse gau stdout into HTTP/HTTPS URLs."""
    urls = {
        candidate
        for line in output.splitlines()
        if (candidate := line.strip())
        and (candidate.startswith("http://") or candidate.startswith("https://"))
    }
    return sorted(urls)


def _normalize_targets(targets: str | Sequence[str]) -> list[str]:
    """Normalize domain or host inputs into a list of non-empty target strings."""
    if isinstance(targets, str):
        values = [targets]
    else:
        values = list(targets)
    return [value.strip() for value in values if value.strip()]
