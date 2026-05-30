"""Rule-based asset prioritization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class PrioritizedAsset:
    """One prioritized asset with explainable scoring reasons."""

    url: str
    score: int
    reasons: list[str]


def score_asset(
    url: str,
    *,
    new_subdomains: list[str],
    new_live_urls: list[str],
    new_technologies: list[str],
    technologies: list[str],
    screenshot_urls: list[str],
) -> PrioritizedAsset:
    """Score one live URL using explicit deterministic rules."""
    score = 0
    reasons: list[str] = []
    hostname = urlparse(url).hostname or ""
    lowered_url = url.lower()

    if hostname in set(new_subdomains):
        score += 5
        reasons.append("New subdomain")
    if url in set(new_live_urls):
        score += 5
        reasons.append("New live URL")
    if set(technologies) & set(new_technologies):
        score += 4
        reasons.append("New technology")
    if any(keyword in lowered_url for keyword in ("admin", "login", "auth")):
        score += 3
        reasons.append("Login/admin/auth keyword")
    if "api" in lowered_url:
        score += 2
        reasons.append("API keyword")
    if url in set(screenshot_urls):
        score += 1
        reasons.append("Screenshot available")

    return PrioritizedAsset(url=url, score=score, reasons=reasons)


def prioritize_assets(
    live_urls: list[str],
    *,
    technology_fingerprints: dict[str, list[str]],
    new_subdomains: list[str],
    new_live_urls: list[str],
    new_technologies: list[str],
    screenshot_urls: list[str],
) -> list[PrioritizedAsset]:
    """Return live URLs sorted by descending priority score."""
    assets = [
        score_asset(
            url,
            new_subdomains=new_subdomains,
            new_live_urls=new_live_urls,
            new_technologies=new_technologies,
            technologies=technology_fingerprints.get(url, []),
            screenshot_urls=screenshot_urls,
        )
        for url in sorted(set(live_urls))
    ]
    return sorted(assets, key=lambda asset: (-asset.score, asset.url))


def summarize_priorities(assets: list[PrioritizedAsset]) -> dict[str, int]:
    """Summarize prioritized asset counts."""
    return {
        "total": len(assets),
        "high_interest": len([asset for asset in assets if asset.score > 0]),
    }
