"""Rule-based technology categorization helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping

CATEGORY_ORDER = (
    "Infrastructure",
    "Framework",
    "CMS",
    "Identity",
    "Language",
    "Unknown",
)

TECHNOLOGY_CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "Infrastructure": (
        "cloudflare",
        "akamai",
        "fastly",
        "cloudfront",
        "nginx",
        "apache",
        "iis",
        "caddy",
    ),
    "Framework": (
        "react",
        "react.js",
        "next.js",
        "nextjs",
        "vue",
        "vue.js",
        "angular",
        "angular.js",
        "django",
        "flask",
        "fastapi",
        "rails",
        "laravel",
        "express",
    ),
    "CMS": (
        "wordpress",
        "drupal",
        "joomla",
        "ghost",
    ),
    "Identity": (
        "keycloak",
        "auth0",
        "okta",
        "azure ad",
        "azure active directory",
    ),
    "Language": (
        "php",
        "asp.net",
        "asp net",
        "node.js",
        "nodejs",
        "python",
        "java",
        "ruby",
    ),
}


def categorize_technology(technology: str) -> str:
    """Return the simple category for one technology name."""
    normalized = technology.strip().lower()
    if not normalized:
        return "Unknown"
    for category in CATEGORY_ORDER:
        if category == "Unknown":
            continue
        if any(
            _matches_alias(normalized, alias)
            for alias in TECHNOLOGY_CATEGORY_RULES[category]
        ):
            return category
    return "Unknown"


def categorize_technologies(technologies: Mapping[str, int]) -> dict[str, dict[str, int]]:
    """Group technology counts by category in a deterministic order."""
    categorized: dict[str, dict[str, int]] = {category: {} for category in CATEGORY_ORDER}
    for technology, count in sorted(technologies.items()):
        category = categorize_technology(technology)
        categorized[category][technology] = count
    grouped: dict[str, dict[str, int]] = {}
    for category in CATEGORY_ORDER:
        category_items = categorized[category]
        if category_items:
            grouped[category] = dict(sorted(category_items.items()))
    return grouped


def summarize_categories(categories: Mapping[str, Mapping[str, int]]) -> dict[str, int]:
    """Summarize total technology counts per category."""
    ordered_summary: dict[str, int] = {}
    for category in CATEGORY_ORDER:
        values = categories.get(category)
        if values:
            ordered_summary[category] = sum(values.values())
    for category in sorted(
        category for category in categories if category not in CATEGORY_ORDER
    ):
        values = categories.get(category)
        if values:
            ordered_summary[category] = sum(values.values())
    return ordered_summary


def _matches_alias(value: str, alias: str) -> bool:
    """Return True when an alias appears as a whole token sequence."""
    pattern = rf"\b{re.escape(alias)}\b"
    return re.search(pattern, value) is not None
