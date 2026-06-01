"""Deterministic intelligence for passively collected historical URLs."""

from __future__ import annotations

import csv
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import parse_qsl, urlparse


class HistoricalUrlConfidence(StrEnum):
    """Confidence derived from explicit URL evidence."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class HistoricalUrlFinding:
    """One explainable classification for a passively collected historical URL."""

    url: str
    hostname: str
    path: str
    query_keys: tuple[str, ...]
    categories: tuple[str, ...]
    sources: tuple[str, ...]
    confidence: HistoricalUrlConfidence
    reasons: tuple[str, ...]


HISTORICAL_OBSERVATION_TYPE = "Historical Lead"
HISTORICAL_REACHABILITY = "unverified"

CATEGORY_ORDER = (
    "Authentication",
    "Administrative",
    "API",
    "Documentation",
    "CMS",
    "Form",
    "Commerce",
    "Redirect Candidate",
    "Public Metadata",
    "JavaScript",
    "Source Map",
    "Archive Indicator",
    "Config Indicator",
    "Static Asset",
    "Media",
    "Feed",
    "Tracking",
    "Unknown",
)

KEYWORD_CATEGORIES: Mapping[str, tuple[str, ...]] = {
    "Authentication": ("login", "logout", "signin", "sign-in", "signup", "register", "oauth"),
    "Administrative": ("admin", "administrator", "dashboard", "manage", "management"),
    "API": ("api", "graphql", "swagger", "openapi"),
    "Documentation": ("docs", "documentation", "swagger", "openapi", "redoc"),
    "CMS": ("wp-admin", "wp-login", "wp-content", "wordpress", "drupal", "joomla"),
    "Form": ("form", "contact", "submit", "feedback"),
    "Commerce": ("cart", "checkout", "payment", "shop", "store", "order"),
    "Public Metadata": ("robots.txt", "sitemap", "security.txt", ".well-known"),
    "Archive Indicator": ("archive", "backup", "old", "legacy"),
    "Config Indicator": ("config", "configuration", ".env", "settings"),
    "Feed": ("feed", "rss", "atom"),
    "Tracking": ("analytics", "tracking", "pixel", "utm_"),
}

REDIRECT_QUERY_KEYS = frozenset(
    {
        "continue",
        "dest",
        "destination",
        "next",
        "redirect",
        "redirect_to",
        "redirect_uri",
        "return",
        "return_to",
        "url",
    }
)
JAVASCRIPT_SUFFIXES = frozenset({".js", ".mjs"})
SOURCE_MAP_SUFFIXES = frozenset({".map"})
STATIC_SUFFIXES = frozenset(
    {".css", ".eot", ".ico", ".svg", ".ttf", ".woff", ".woff2"}
)
MEDIA_SUFFIXES = frozenset(
    {".avi", ".gif", ".jpeg", ".jpg", ".mov", ".mp3", ".mp4", ".png", ".webp"}
)
ARCHIVE_SUFFIXES = frozenset({".7z", ".bak", ".gz", ".rar", ".tar", ".tgz", ".zip"})
CONFIG_SUFFIXES = frozenset({".conf", ".config", ".env", ".ini", ".toml", ".yaml", ".yml"})

_CATEGORY_INDEX = {category: index for index, category in enumerate(CATEGORY_ORDER)}
_LEAD_CATEGORY_WEIGHTS = {
    "Config Indicator": 100,
    "Authentication": 90,
    "Administrative": 85,
    "API": 80,
    "Public Metadata": 75,
    "Source Map": 70,
    "CMS": 65,
    "Redirect Candidate": 60,
    "Documentation": 45,
    "Form": 40,
    "Commerce": 35,
    "Archive Indicator": 30,
    "Feed": 10,
    "JavaScript": 5,
    "Unknown": 0,
    "Tracking": -5,
    "Static Asset": -10,
    "Media": -15,
}


def classify_historical_urls(
    urls_by_source: Mapping[str, list[str]],
) -> list[HistoricalUrlFinding]:
    """Classify merged passive historical URLs while preserving provenance."""
    provenance: dict[str, set[str]] = {}
    for source, urls in sorted(urls_by_source.items()):
        for url in urls:
            provenance.setdefault(url, set()).add(source)
    return [
        classify_historical_url(url, sources=sorted(sources))
        for url, sources in sorted(provenance.items())
    ]


def classify_historical_url(
    url: str,
    *,
    sources: list[str] | tuple[str, ...] = (),
) -> HistoricalUrlFinding:
    """Classify one historical URL from deterministic URL-only evidence."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    query_keys = tuple(
        sorted({key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)})
    )
    searchable = f"{hostname}{path}?{'&'.join(query_keys)}".lower()
    suffix = Path(path.lower()).suffix
    evidence: dict[str, set[str]] = {}

    for category, keywords in KEYWORD_CATEGORIES.items():
        matches = sorted(keyword for keyword in keywords if _keyword_matches(searchable, keyword))
        if matches:
            evidence.setdefault(category, set()).add("keyword: " + ", ".join(matches))
    if any(key in REDIRECT_QUERY_KEYS for key in query_keys):
        matches = sorted(set(query_keys) & REDIRECT_QUERY_KEYS)
        evidence.setdefault("Redirect Candidate", set()).add("query key: " + ", ".join(matches))
    if suffix in JAVASCRIPT_SUFFIXES:
        evidence.setdefault("JavaScript", set()).add(f"file suffix: {suffix}")
    if suffix in SOURCE_MAP_SUFFIXES:
        evidence.setdefault("Source Map", set()).add(f"file suffix: {suffix}")
    if suffix in STATIC_SUFFIXES:
        evidence.setdefault("Static Asset", set()).add(f"file suffix: {suffix}")
    if suffix in MEDIA_SUFFIXES:
        evidence.setdefault("Media", set()).add(f"file suffix: {suffix}")
    if suffix in ARCHIVE_SUFFIXES:
        evidence.setdefault("Archive Indicator", set()).add(f"file suffix: {suffix}")
    if suffix in CONFIG_SUFFIXES:
        evidence.setdefault("Config Indicator", set()).add(f"file suffix: {suffix}")

    if not evidence:
        evidence["Unknown"] = {"no configured URL indicator matched"}
    categories = tuple(sorted(evidence, key=lambda category: _CATEGORY_INDEX[category]))
    reasons = tuple(
        f"{category}: {reason}"
        for category in categories
        for reason in sorted(evidence[category])
    )
    return HistoricalUrlFinding(
        url=url,
        hostname=hostname,
        path=path,
        query_keys=query_keys,
        categories=categories,
        sources=tuple(sorted(set(sources))),
        confidence=_confidence(evidence),
        reasons=reasons,
    )


def summarize_historical_urls(findings: list[HistoricalUrlFinding]) -> dict[str, int]:
    """Count classified historical leads by category."""
    return {
        category: sum(category in finding.categories for finding in findings)
        for category in CATEGORY_ORDER
        if any(category in finding.categories for finding in findings)
    }


def top_historical_leads(
    findings: list[HistoricalUrlFinding],
    *,
    limit: int = 25,
) -> list[HistoricalUrlFinding]:
    """Return the highest-interest historical leads in deterministic order."""
    return sorted(findings, key=_lead_sort_key)[:limit]


def write_historical_url_tsv(
    findings: list[HistoricalUrlFinding],
    output_path: Path,
) -> Path:
    """Write the full classified historical URL set as human-readable TSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "url",
                "observation_type",
                "reachability",
                "hostname",
                "path",
                "query_keys",
                "categories",
                "sources",
                "confidence",
                "reasons",
            )
        )
        for finding in sorted(findings, key=lambda item: item.url):
            writer.writerow(
                (
                    finding.url,
                    HISTORICAL_OBSERVATION_TYPE,
                    HISTORICAL_REACHABILITY,
                    finding.hostname,
                    finding.path,
                    ",".join(finding.query_keys),
                    ",".join(finding.categories),
                    ",".join(finding.sources),
                    finding.confidence.value,
                    " | ".join(finding.reasons),
                )
            )
    return output_path


def _confidence(evidence: Mapping[str, set[str]]) -> HistoricalUrlConfidence:
    """Derive confidence from explicit indicator strength and diversity."""
    categories = set(evidence)
    if categories == {"Unknown"}:
        return HistoricalUrlConfidence.LOW
    if categories & {"Source Map", "Config Indicator"}:
        return HistoricalUrlConfidence.HIGH
    if len(categories) >= 2:
        return HistoricalUrlConfidence.HIGH
    return HistoricalUrlConfidence.MEDIUM


def _keyword_matches(searchable: str, keyword: str) -> bool:
    """Match readable URL tokens without broad substring false positives."""
    if keyword.endswith("_"):
        return keyword in searchable
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", searchable) is not None


def _lead_sort_key(finding: HistoricalUrlFinding) -> tuple[int, int, int, str]:
    """Sort high-interest historical leads before low-signal static content."""
    category_weight = max(_LEAD_CATEGORY_WEIGHTS[category] for category in finding.categories)
    confidence_weight = {
        HistoricalUrlConfidence.HIGH: 2,
        HistoricalUrlConfidence.MEDIUM: 1,
        HistoricalUrlConfidence.LOW: 0,
    }[finding.confidence]
    return (-category_weight, -confidence_weight, -len(finding.sources), finding.url)
