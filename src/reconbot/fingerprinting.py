"""Passive technology fingerprinting helpers."""

from __future__ import annotations

import json
import logging
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

from reconbot.tools.httpx import run_fingerprint_probe

LOGGER = logging.getLogger(__name__)
DEFAULT_BINARY = "httpx"
DEFAULT_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True, slots=True)
class PassiveAssetMetadata:
    """Passive metadata returned by httpx for one asset."""

    technologies: list[str] = field(default_factory=list)
    response_headers: dict[str, str] = field(default_factory=dict)
    title: str = ""
    platform_indicators: list[str] = field(default_factory=list)


def fingerprint_url(
    url: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Use httpx passive technology detection for one live URL."""
    return fingerprint_url_metadata(url, binary=binary, timeout=timeout).technologies


def fingerprint_url_metadata(
    url: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> PassiveAssetMetadata:
    """Use httpx to collect passive metadata for one live URL."""
    target = url.strip()
    if not target:
        return PassiveAssetMetadata()

    result = run_fingerprint_probe(target, binary=binary, timeout=timeout)
    if not result.success:
        LOGGER.warning("httpx technology fingerprinting failed for %s", target)
        return PassiveAssetMetadata()

    return _parse_httpx_metadata(result.output)


def fingerprint_urls(
    urls: list[str],
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    metadata: dict[str, PassiveAssetMetadata] | None = None,
) -> dict[str, list[str]]:
    """Fingerprint live URLs and return technologies keyed by URL."""
    fingerprints: dict[str, list[str]] = {}
    for url in urls:
        target = url.strip()
        if not target:
            continue
        asset_metadata = fingerprint_url_metadata(target, binary=binary, timeout=timeout)
        fingerprints[target] = asset_metadata.technologies
        if metadata is not None:
            metadata[target] = asset_metadata
    return fingerprints


def summarize_technologies(fingerprints: Mapping[str, list[str]]) -> dict[str, int]:
    """Count technologies across fingerprinted URLs."""
    counts: Counter[str] = Counter()
    for technologies in fingerprints.values():
        counts.update(set(technologies))
    return dict(sorted(counts.items()))


def _parse_httpx_technologies(output: str) -> list[str]:
    """Parse httpx JSON output into sorted unique technology names."""
    return _parse_httpx_metadata(output).technologies


def _parse_httpx_metadata(output: str) -> PassiveAssetMetadata:
    """Parse httpx JSON output into passive asset metadata."""
    technologies: set[str] = set()
    response_headers: dict[str, str] = {}
    titles: set[str] = set()
    platform_indicators: set[str] = set()
    for line in output.splitlines():
        if not (payload := line.strip()):
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        technologies.update(_extract_technology_values(data))
        response_headers.update(_extract_headers(data))
        titles.update(_as_strings(data.get("title")) if isinstance(data, dict) else [])
        if isinstance(data, dict):
            platform_indicators.update(_as_strings(data.get("cdn_name")))
            platform_indicators.update(_as_strings(data.get("cdn")))
            platform_indicators.update(_as_strings(data.get("cname")))
    return PassiveAssetMetadata(
        technologies=sorted(technologies),
        response_headers=dict(sorted(response_headers.items())),
        title=sorted(titles)[0] if titles else "",
        platform_indicators=sorted(platform_indicators),
    )


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


def _extract_headers(data: object) -> dict[str, str]:
    """Extract string response headers from common httpx JSON fields."""
    if not isinstance(data, dict):
        return {}
    for key in ("header", "response_header"):
        value = data.get(key)
        if isinstance(value, dict):
            return {
                str(name): header_value
                for name, header_value in value.items()
                if isinstance(header_value, str)
            }
    return {}
