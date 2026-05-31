"""Rule-based technology categorization helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

CATEGORY_ORDER = (
    "Infrastructure",
    "Framework",
    "CMS",
    "Identity",
    "Language",
    "Unknown",
)
ASSET_CATEGORY_ORDER = (
    "Authentication",
    "API",
    "Administrative",
    "Commerce",
    "CDN",
    "Marketing",
    "Documentation",
    "Developer Tools",
    "Source Control",
    "Monitoring",
    "Cloud Infrastructure",
    "SaaS Platforms",
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
ASSET_CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "Authentication": ("auth0", "keycloak", "okta", "login", "sign in", "sso", "oauth"),
    "API": ("api", "graphql", "swagger", "openapi", "fastapi"),
    "Administrative": ("admin", "administrator", "dashboard", "control panel"),
    "Commerce": ("shopify", "stripe", "magento", "woocommerce", "commerce", "checkout"),
    "CDN": ("cloudflare", "akamai", "fastly", "cloudfront", "cdn"),
    "Marketing": ("hubspot", "marketo", "mailchimp", "segment", "analytics"),
    "Documentation": ("swagger", "openapi", "redoc", "documentation", "docs"),
    "Developer Tools": ("jenkins", "gitlab", "github", "jira", "sentry", "developer"),
    "Source Control": ("gitlab", "github", "bitbucket", "gitea", "source control"),
    "Monitoring": ("grafana", "prometheus", "datadog", "new relic", "statuspage", "sentry"),
    "Cloud Infrastructure": (
        "aws",
        "amazon web services",
        "azure",
        "google cloud",
        "cloudfront",
        "s3",
    ),
    "SaaS Platforms": ("salesforce", "zendesk", "atlassian", "slack", "notion", "workday"),
}


class Confidence(StrEnum):
    """Human-readable asset category confidence levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class AssetCategory:
    """One passive category match for an asset."""

    category: str
    confidence: Confidence
    indicators: tuple[str, ...]


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


def categorize_assets(
    technology_fingerprints: Mapping[str, list[str]],
    *,
    response_headers: Mapping[str, Mapping[str, str]] | None = None,
    page_titles: Mapping[str, str] | None = None,
    platform_indicators: Mapping[str, list[str]] | None = None,
) -> dict[str, list[AssetCategory]]:
    """Categorize assets from passive metadata in deterministic order."""
    headers = response_headers or {}
    titles = page_titles or {}
    platforms = platform_indicators or {}
    urls = sorted(set(technology_fingerprints) | set(headers) | set(titles) | set(platforms))
    return {
        url: _categorize_asset(
            url,
            technologies=technology_fingerprints.get(url, []),
            headers=headers.get(url, {}),
            title=titles.get(url, ""),
            platforms=platforms.get(url, []),
        )
        for url in urls
    }


def summarize_asset_categories(
    assets: Mapping[str, list[AssetCategory]],
) -> dict[str, int]:
    """Count categorized assets once per category."""
    counts = {
        category: sum(
            any(match.category == category for match in matches)
            for matches in assets.values()
        )
        for category in ASSET_CATEGORY_ORDER
    }
    return {category: count for category, count in counts.items() if count}


def _categorize_asset(
    url: str,
    *,
    technologies: list[str],
    headers: Mapping[str, str],
    title: str,
    platforms: list[str],
) -> list[AssetCategory]:
    """Categorize one asset using passive metadata signals."""
    signals = _asset_signals(url, technologies, headers, title, platforms)
    matches: list[AssetCategory] = []
    for category in ASSET_CATEGORY_ORDER:
        indicators = tuple(
            sorted(
                {
                    f"{source}: {value}"
                    for source, value in signals
                    if any(
                        _matches_alias(value.lower(), alias)
                        for alias in ASSET_CATEGORY_RULES[category]
                    )
                }
            )
        )
        if indicators:
            matches.append(
                AssetCategory(
                    category=category,
                    confidence=_confidence(indicators),
                    indicators=indicators,
                )
            )
    return matches


def _asset_signals(
    url: str,
    technologies: list[str],
    headers: Mapping[str, str],
    title: str,
    platforms: list[str],
) -> list[tuple[str, str]]:
    """Return normalized passive signals for one asset."""
    signals = [("url", url)]
    signals.extend(("technology", value) for value in technologies if value.strip())
    signals.extend(
        ("header", f"{name}: {value}")
        for name, value in sorted(headers.items())
        if name.strip() and value.strip()
    )
    if title.strip():
        signals.append(("title", title))
    signals.extend(("platform", value) for value in platforms if value.strip())
    return signals


def _confidence(indicators: tuple[str, ...]) -> Confidence:
    """Assign confidence from the number and quality of passive signals."""
    sources = {indicator.split(":", maxsplit=1)[0] for indicator in indicators}
    if "technology" in sources or "platform" in sources or len(sources) >= 2:
        return Confidence.HIGH
    if "header" in sources or "title" in sources:
        return Confidence.MEDIUM
    return Confidence.LOW


def _matches_alias(value: str, alias: str) -> bool:
    """Return True when an alias appears as a whole token sequence."""
    pattern = rf"\b{re.escape(alias)}\b"
    return re.search(pattern, value) is not None
