"""Passive technology fingerprinting helpers."""

from __future__ import annotations

import json
import logging
from collections import Counter
from collections.abc import Mapping

from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_BINARY = "httpx"
DEFAULT_TIMEOUT_SECONDS = 120.0


def fingerprint_url(
    url: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Use httpx passive technology detection for one live URL."""
    target = url.strip()
    if not target:
        return []

    result = run_command(
        "httpx",
        [binary, "-silent", "-json", "-tech-detect", "-u", target],
        timeout=timeout,
    )
    if not result.success:
        LOGGER.warning("httpx technology fingerprinting failed for %s", target)
        return []

    return _parse_httpx_technologies(result.output)


def fingerprint_urls(
    urls: list[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, list[str]]:
    """Fingerprint live URLs and return technologies keyed by URL."""
    fingerprints: dict[str, list[str]] = {}
    for url in urls:
        target = url.strip()
        if not target:
            continue
        technologies = fingerprint_url(target, binary=binary, timeout=timeout)
        fingerprints[target] = technologies
    return fingerprints


def summarize_technologies(fingerprints: Mapping[str, list[str]]) -> dict[str, int]:
    """Count technologies across fingerprinted URLs."""
    counts: Counter[str] = Counter()
    for technologies in fingerprints.values():
        counts.update(set(technologies))
    return dict(sorted(counts.items()))


def _parse_httpx_technologies(output: str) -> list[str]:
    """Parse httpx JSON output into sorted unique technology names."""
    technologies: set[str] = set()
    for line in output.splitlines():
        if not (payload := line.strip()):
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        technologies.update(_extract_technology_values(data))
    return sorted(technologies)


def _extract_technology_values(data: object) -> list[str]:
    """Extract common httpx technology fields from a JSON object."""
    if not isinstance(data, dict):
        return []

    values: list[str] = []
    values.extend(_as_strings(data.get("tech")))
    values.extend(_as_strings(data.get("technologies")))
    values.extend(_as_strings(data.get("webserver")))
    values.extend(_as_strings(data.get("cdn_name")))
    values.extend(_as_strings(data.get("cdn")))
    values.extend(_as_strings(data.get("framework")))
    values.extend(_as_strings(data.get("cms")))
    values.extend(_as_strings(data.get("language")))
    return values


def _as_strings(value: object) -> list[str]:
    """Normalize JSON values into non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []
