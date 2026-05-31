from reconbot.guidance import (
    AUTHORIZED_SAFETY_NOTE,
    build_investigation_plan,
    suggest_checks_for_asset,
    summarize_guidance,
)
from reconbot.prioritization import PrioritizedAsset
from reconbot.technology_categories import AssetCategory, Confidence


def test_suggest_checks_for_authentication_asset_is_safe_and_explainable() -> None:
    guidance = suggest_checks_for_asset(
        "https://login.example.com",
        asset_categories=[
            AssetCategory("Authentication", Confidence.HIGH, ("technology: Auth0",)),
        ],
        technologies=["Auth0"],
        high_interest_score=9,
        is_new_asset=True,
        has_screenshot=True,
    )

    assert guidance.url == "https://login.example.com"
    assert "Matched guidance category: Authentication" in guidance.reasons
    assert "Observed technologies: Auth0" in guidance.reasons
    assert "High-interest score: 9" in guidance.reasons
    assert "New live asset" in guidance.reasons
    assert "Screenshot available" in guidance.reasons
    assert [check.title for check in guidance.checks if check.category == "Authentication"] == [
        "Password reset flow review",
        "Session and logout behavior",
        "Account enumeration indicators",
        "MFA presence check",
    ]
    assert all(check.safety_note == AUTHORIZED_SAFETY_NOTE for check in guidance.checks)


def test_suggest_checks_uses_url_keywords_and_cms_technology() -> None:
    guidance = suggest_checks_for_asset(
        "https://staging.example.com/admin/api",
        asset_categories=[],
        technologies=["WordPress"],
        high_interest_score=0,
        is_new_asset=False,
        has_screenshot=False,
    )

    categories = {check.category for check in guidance.checks}
    assert categories == {"General", "API", "Administrative", "Staging/Dev", "CMS"}


def test_build_investigation_plan_preserves_priority_order() -> None:
    plan = build_investigation_plan(
        [
            PrioritizedAsset("https://admin.example.com", 8, ["Login/admin/auth keyword"]),
            PrioritizedAsset("https://plain.example.com", 0, []),
        ],
        asset_categories={},
        technology_fingerprints={},
        new_live_urls=["https://admin.example.com"],
        screenshot_urls=["https://admin.example.com"],
    )

    assert [asset.url for asset in plan] == [
        "https://admin.example.com",
        "https://plain.example.com",
    ]
    assert "New live asset" in plan[0].reasons
    assert "Screenshot available" in plan[0].reasons
    assert plan[1].checks[0].category == "General"


def test_summarize_guidance_counts_checks_by_category() -> None:
    guidance = suggest_checks_for_asset(
        "https://api.example.com",
        asset_categories=[],
        technologies=[],
        high_interest_score=0,
        is_new_asset=False,
        has_screenshot=False,
    )

    assert summarize_guidance([guidance]) == {"API": 4, "General": 4}
