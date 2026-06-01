"""Lightweight wrapper for the httpx CLI."""

from __future__ import annotations

import logging

from reconbot.collection_status import CollectionStatus, status_from_result
from reconbot.models import ToolResult
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "httpx"


def find_live_urls(
    subdomains: list[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    collection_statuses: list[CollectionStatus] | None = None,
) -> list[str]:
    """Run httpx for subdomains and return sorted unique live HTTP/HTTPS URLs."""
    live_urls: set[str] = set()
    for subdomain in subdomains:
        target = subdomain.strip()
        if not target:
            continue

        result = run_command(
            "httpx",
            [binary, "-silent", "-u", target],
            timeout=timeout,
        )
        parsed_urls = parse_live_urls(result.output) if result.success else []
        if collection_statuses is not None:
            collection_statuses.append(
                status_from_result(
                    source="httpx",
                    target=target,
                    result=result,
                    result_count=len(parsed_urls),
                )
            )
        if not result.success:
            LOGGER.warning("httpx failed for %s with code %s", target, result.return_code)
            continue

        live_urls.update(parsed_urls)

    return sorted(live_urls)


def parse_live_urls(output: str) -> list[str]:
    """Parse httpx stdout into HTTP/HTTPS URLs."""
    urls = {
        candidate
        for line in output.splitlines()
        if (candidate := line.strip().lower().rstrip("/"))
        and (candidate.startswith("http://") or candidate.startswith("https://"))
    }
    return sorted(urls)


def run_fingerprint_probe(
    target: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> ToolResult:
    """Run one passive httpx metadata probe."""
    return run_command(
        "httpx",
        [
            binary,
            "-silent",
            "-json",
            "-tech-detect",
            "-title",
            "-include-response-header",
            "-u",
            target,
        ],
        timeout=timeout,
    )
