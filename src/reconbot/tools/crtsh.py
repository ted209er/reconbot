"""Passive crt.sh certificate transparency lookup."""

from __future__ import annotations

import json
import logging

from reconbot.tools.subfinder import parse_subdomains
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_BINARY = "curl"


def find_subdomains(
    domain: str,
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[str]:
    """Query crt.sh for a domain and return sorted unique subdomains."""
    result = run_command(
        "crtsh",
        [binary, "-fsSL", f"https://crt.sh/?q=%25.{domain}&output=json"],
        timeout=timeout,
    )
    if not result.success:
        LOGGER.warning("crt.sh lookup failed for %s with code %s", domain, result.return_code)
        return []

    return parse_crtsh_subdomains(result.output, domain)


def parse_crtsh_subdomains(output: str, domain: str) -> list[str]:
    """Parse crt.sh JSON output into normalized subdomains."""
    try:
        rows = json.loads(output)
    except json.JSONDecodeError:
        return []
    if not isinstance(rows, list):
        return []

    names: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            names.extend(_name_values(row.get("name_value")))
            names.extend(_name_values(row.get("common_name")))
    return parse_subdomains("\n".join(names), domain)


def _name_values(value: object) -> list[str]:
    """Return certificate names from a crt.sh field."""
    if not isinstance(value, str):
        return []
    return [line.strip().removeprefix("*.") for line in value.splitlines() if line.strip()]
