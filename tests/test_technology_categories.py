from reconbot.technology_categories import (
    categorize_technologies,
    categorize_technology,
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
