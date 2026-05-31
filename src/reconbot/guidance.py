"""Safe manual investigation guidance for authorized reconnaissance."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from reconbot.prioritization import PrioritizedAsset
from reconbot.technology_categories import AssetCategory, categorize_technology

AUTHORIZED_SAFETY_NOTE = (
    "Use only authorized targets, owned test accounts, and non-destructive validation. "
    "Do not access third-party user data."
)


@dataclass(frozen=True, slots=True)
class SuggestedCheck:
    """One explainable safe manual investigation check."""

    category: str
    title: str
    why_it_matters: str
    safe_manual_approach: str
    evidence_to_collect: str
    safety_note: str = AUTHORIZED_SAFETY_NOTE


@dataclass(frozen=True, slots=True)
class AssetGuidance:
    """Suggested manual checks for one discovered asset."""

    url: str
    reasons: tuple[str, ...]
    checks: tuple[SuggestedCheck, ...]


CHECK_TEMPLATES: dict[str, tuple[SuggestedCheck, ...]] = {
    "Authentication": (
        SuggestedCheck(
            "Authentication",
            "Password reset flow review",
            "Reset flows can reveal account state or weak recovery boundaries.",
            "Review the reset flow manually with owned test accounts and benign inputs only.",
            "Record visible steps, generic or account-specific messages, and screenshots.",
        ),
        SuggestedCheck(
            "Authentication",
            "Session and logout behavior",
            "Clear session invalidation helps reduce unintended account access.",
            "Using an owned test account, sign in and sign out normally, then confirm "
            "the session ends.",
            "Record logout behavior, session state observations, and screenshots.",
        ),
        SuggestedCheck(
            "Authentication",
            "Account enumeration indicators",
            "Different responses can disclose whether an account exists.",
            "Compare normal UI messages for owned test accounts and clearly invalid "
            "placeholders only.",
            "Record response wording, status behavior, and timestamps without repeated guessing.",
        ),
        SuggestedCheck(
            "Authentication",
            "MFA presence check",
            "MFA availability is relevant to account protection review.",
            "Inspect account security settings for an owned test account.",
            "Record available MFA options and screenshots.",
        ),
    ),
    "API": (
        SuggestedCheck(
            "API",
            "API documentation review",
            "Public documentation can clarify intended endpoints and authorization boundaries.",
            "Review linked or discovered documentation manually without automated enumeration.",
            "Record documentation URLs, described authentication, and relevant screenshots.",
        ),
        SuggestedCheck(
            "API",
            "Authorization boundary checks with owned test accounts",
            "APIs should enforce account boundaries consistently.",
            "Compare permitted actions using owned test accounts only and non-destructive "
            "requests.",
            "Record account roles, expected behavior, actual behavior, and timestamps.",
        ),
        SuggestedCheck(
            "API",
            "Object ID access checks with owned objects",
            "Object references should not cross authorized ownership boundaries.",
            "Use objects created by owned test accounts only and compare expected access behavior.",
            "Record owned object IDs, test-account roles, and observed responses.",
        ),
        SuggestedCheck(
            "API",
            "Excessive error detail",
            "Verbose errors can disclose implementation details.",
            "Review normal error responses caused by benign invalid input.",
            "Record status codes and redacted error text.",
        ),
    ),
    "Administrative": (
        SuggestedCheck(
            "Administrative",
            "Exposed admin panel review",
            "Administrative surfaces warrant careful access-boundary review.",
            "Open the discovered page manually and verify that unauthenticated access is limited.",
            "Record the URL, redirect behavior, visible branding, and screenshots.",
        ),
        SuggestedCheck(
            "Administrative",
            "Default page or staging banner review",
            "Default pages and banners can disclose deployment state.",
            "Inspect the visible page for default content, staging labels, and environment "
            "references.",
            "Record page title, visible banners, and screenshots.",
        ),
        SuggestedCheck(
            "Administrative",
            "Access control boundary checks",
            "Administrative functions should remain restricted to authorized roles.",
            "Compare visible navigation and allowed actions using owned test accounts with "
            "approved roles.",
            "Record account roles, visible actions, and non-destructive outcomes.",
        ),
    ),
    "Staging/Dev": (
        SuggestedCheck(
            "Staging/Dev",
            "Debug mode indicators",
            "Debug output can reveal sensitive implementation details.",
            "Inspect visible pages and benign error states for debug banners or stack details.",
            "Record redacted messages, page titles, and screenshots.",
        ),
        SuggestedCheck(
            "Staging/Dev",
            "Exposed environment or config references",
            "Public environment references can disclose deployment details.",
            "Review visible source links, page content, and normal responses manually.",
            "Record URLs and redacted references without downloading sensitive material.",
        ),
        SuggestedCheck(
            "Staging/Dev",
            "Test data indicators",
            "Test data can reveal an unintended public deployment.",
            "Inspect visible content for sample users, fixtures, or non-production labels.",
            "Record redacted examples and screenshots.",
        ),
        SuggestedCheck(
            "Staging/Dev",
            "Public directory or listing indicators",
            "Visible listings can expose unintended public files.",
            "Review listings only when directly linked or visibly exposed; do not enumerate paths.",
            "Record the exposed URL, visible filenames, and screenshots.",
        ),
    ),
    "CMS": (
        SuggestedCheck(
            "CMS",
            "Exposed version information",
            "Visible CMS version details can help an authorized reviewer assess maintenance "
            "status.",
            "Inspect page source, visible metadata, and normal response headers manually.",
            "Record the URL and visible version indicators.",
        ),
        SuggestedCheck(
            "CMS",
            "Public plugin or theme indicators",
            "Publicly visible component names can clarify the exposed application surface.",
            "Review linked public assets and visible source references only.",
            "Record component names and source URLs without enumeration.",
        ),
        SuggestedCheck(
            "CMS",
            "CMS admin exposure",
            "CMS administrative routes should enforce access controls.",
            "Review directly linked or already discovered admin surfaces manually.",
            "Record URL, redirect behavior, and screenshots.",
        ),
    ),
    "General": (
        SuggestedCheck(
            "General",
            "Security headers review",
            "Security headers help browsers apply expected protections.",
            "Review response headers already captured by Reconbot or inspect them manually.",
            "Record relevant headers and observed values.",
        ),
        SuggestedCheck(
            "General",
            "CORS behavior review",
            "CORS configuration should reflect intended trusted origins.",
            "Review normal browser behavior and documented API responses using an "
            "authorized origin.",
            "Record observed allow-origin behavior and the tested authorized origin.",
        ),
        SuggestedCheck(
            "General",
            "Verbose errors",
            "Verbose errors can disclose implementation details.",
            "Review benign invalid input through normal UI paths only.",
            "Record redacted error messages and timestamps.",
        ),
        SuggestedCheck(
            "General",
            "Sensitive public files",
            "Directly exposed public files can disclose unintended information.",
            "Review only files already linked, reported, or visibly exposed; do not "
            "enumerate paths.",
            "Record URLs and redacted observations.",
        ),
    ),
}
STAGING_KEYWORDS = ("staging", "stage", "dev", "development", "test", "qa", "debug")
URL_CATEGORY_KEYWORDS = {
    "Authentication": ("login", "auth", "signin", "sso", "oauth"),
    "API": ("api", "graphql", "swagger", "openapi"),
    "Administrative": ("admin", "dashboard", "control-panel"),
}


def suggest_checks_for_asset(
    url: str,
    *,
    asset_categories: list[AssetCategory],
    technologies: list[str],
    high_interest_score: int,
    is_new_asset: bool,
    has_screenshot: bool,
) -> AssetGuidance:
    """Suggest deterministic manual checks from existing passive findings."""
    selected_categories = _guidance_categories(url, asset_categories, technologies)
    reasons = _guidance_reasons(
        selected_categories,
        technologies,
        high_interest_score,
        is_new_asset,
        has_screenshot,
    )
    checks = tuple(
        check
        for category in selected_categories
        for check in CHECK_TEMPLATES[category]
    )
    return AssetGuidance(url=url, reasons=reasons, checks=checks)


def summarize_guidance(guidance: list[AssetGuidance]) -> dict[str, int]:
    """Count suggested checks by category."""
    summary: dict[str, int] = {}
    for asset in guidance:
        for check in asset.checks:
            summary[check.category] = summary.get(check.category, 0) + 1
    return dict(sorted(summary.items()))


def build_investigation_plan(
    assets: list[PrioritizedAsset],
    *,
    asset_categories: Mapping[str, list[AssetCategory]],
    technology_fingerprints: Mapping[str, list[str]],
    new_live_urls: list[str],
    screenshot_urls: list[str],
) -> list[AssetGuidance]:
    """Build a deterministic guidance plan for discovered live assets."""
    new_urls = set(new_live_urls)
    screenshot_url_set = set(screenshot_urls)
    return [
        suggest_checks_for_asset(
            asset.url,
            asset_categories=asset_categories.get(asset.url, []),
            technologies=technology_fingerprints.get(asset.url, []),
            high_interest_score=asset.score,
            is_new_asset=asset.url in new_urls,
            has_screenshot=asset.url in screenshot_url_set,
        )
        for asset in assets
    ]


def _guidance_categories(
    url: str,
    asset_categories: list[AssetCategory],
    technologies: list[str],
) -> tuple[str, ...]:
    """Return applicable guidance categories in a stable order."""
    detected = {match.category for match in asset_categories}
    technology_categories = {categorize_technology(technology) for technology in technologies}
    categories = ["General"]
    for category in ("Authentication", "API", "Administrative"):
        if category in detected or any(
            keyword in url.lower() for keyword in URL_CATEGORY_KEYWORDS[category]
        ):
            categories.append(category)
    if any(keyword in url.lower() for keyword in STAGING_KEYWORDS):
        categories.append("Staging/Dev")
    if "CMS" in technology_categories:
        categories.append("CMS")
    return tuple(categories)


def _guidance_reasons(
    categories: tuple[str, ...],
    technologies: list[str],
    high_interest_score: int,
    is_new_asset: bool,
    has_screenshot: bool,
) -> tuple[str, ...]:
    """Return explainable reasons for suggested checks."""
    reasons = [f"Matched guidance category: {category}" for category in categories]
    if technologies:
        reasons.append("Observed technologies: " + ", ".join(sorted(set(technologies))))
    if high_interest_score:
        reasons.append(f"High-interest score: {high_interest_score}")
    if is_new_asset:
        reasons.append("New live asset")
    if has_screenshot:
        reasons.append("Screenshot available")
    return tuple(reasons)
