from reconbot.technology_categories import (
    Confidence,
    categorize_assets,
    categorize_technologies,
    categorize_technology,
    summarize_asset_categories,
    summarize_categories,
)


def test_categorize_technology_maps_known_values() -> None:
    assert categorize_technology("Cloudflare") == "Infrastructure"
    assert categorize_technology("Next.js") == "Framework"
    assert categorize_technology("WordPress") == "CMS"
    assert categorize_technology("Keycloak") == "Identity"
    assert categorize_technology("Python") == "Language"
    assert categorize_technology("Azure Active Directory") == "Identity"
    assert categorize_technology("NodeJS") == "Language"


def test_categorize_technology_returns_unknown_for_unmatched_values() -> None:
    assert categorize_technology("CustomThing") == "Unknown"
    assert categorize_technology("  ") == "Unknown"


def test_categorize_technologies_groups_and_sorts_values() -> None:
    categories = categorize_technologies(
        {
            "React": 3,
            "Cloudflare": 12,
            "FastAPI": 2,
            "Mystery": 1,
        }
    )

    assert categories == {
        "Infrastructure": {"Cloudflare": 12},
        "Framework": {"FastAPI": 2, "React": 3},
        "Unknown": {"Mystery": 1},
    }


def test_summarize_categories_totals_values() -> None:
    categories = {
        "Infrastructure": {"Cloudflare": 12},
        "Framework": {"FastAPI": 2, "React": 3},
        "Unknown": {"Mystery": 1},
    }

    assert summarize_categories(categories) == {
        "Infrastructure": 12,
        "Framework": 5,
        "Unknown": 1,
    }


def test_categorize_assets_uses_passive_metadata_with_confidence() -> None:
    categories = categorize_assets(
        {
            "https://login.example.com": ["Auth0"],
            "https://status.example.com": [],
            "https://knowledge.example.com": [],
        },
        response_headers={
            "https://status.example.com": {"server": "cloudflare"},
        },
        page_titles={
            "https://knowledge.example.com": "API Documentation",
        },
        platform_indicators={
            "https://status.example.com": ["Statuspage"],
        },
    )

    assert categories["https://login.example.com"][0].category == "Authentication"
    assert categories["https://login.example.com"][0].confidence == Confidence.HIGH
    assert [match.category for match in categories["https://status.example.com"]] == [
        "CDN",
        "Monitoring",
    ]
    assert categories["https://status.example.com"][0].confidence == Confidence.MEDIUM
    assert categories["https://status.example.com"][1].confidence == Confidence.HIGH
    assert [match.category for match in categories["https://knowledge.example.com"]] == [
        "API",
        "Documentation",
    ]
    assert all(
        match.confidence == Confidence.MEDIUM
        for match in categories["https://knowledge.example.com"]
    )


def test_categorize_assets_supports_requested_platform_categories() -> None:
    categories = categorize_assets(
        {"https://example.com": []},
        platform_indicators={
            "https://example.com": [
                "Shopify",
                "GitLab",
                "AWS",
                "Salesforce",
                "Jenkins",
                "HubSpot",
            ]
        },
        page_titles={"https://example.com": "Admin Dashboard"},
    )

    assert [match.category for match in categories["https://example.com"]] == [
        "Administrative",
        "Commerce",
        "Marketing",
        "Developer Tools",
        "Source Control",
        "Cloud Infrastructure",
        "SaaS Platforms",
    ]


def test_summarize_asset_categories_counts_assets_once_per_category() -> None:
    categories = categorize_assets(
        {
            "https://api.example.com": ["FastAPI", "Swagger"],
            "https://docs.example.com": ["Swagger"],
        }
    )

    assert summarize_asset_categories(categories) == {
        "API": 2,
        "Documentation": 2,
    }


def test_categorize_assets_assigns_low_confidence_to_url_only_match() -> None:
    categories = categorize_assets({"https://admin.example.com": []})

    assert categories["https://admin.example.com"][0].category == "Administrative"
    assert categories["https://admin.example.com"][0].confidence == Confidence.LOW
