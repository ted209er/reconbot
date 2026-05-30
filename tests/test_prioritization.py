from reconbot.prioritization import prioritize_assets, score_asset, summarize_priorities


def test_score_asset_uses_explainable_rules() -> None:
    asset = score_asset(
        "https://admin.example.com/login",
        new_subdomains=["admin.example.com"],
        new_live_urls=["https://admin.example.com/login"],
        new_technologies=["FastAPI"],
        technologies=["FastAPI"],
        screenshot_urls=["https://admin.example.com/login"],
    )

    assert asset.score == 18
    assert asset.reasons == [
        "New subdomain",
        "New live URL",
        "New technology",
        "Login/admin/auth keyword",
        "Screenshot available",
    ]


def test_score_asset_adds_api_keyword() -> None:
    asset = score_asset(
        "https://api.example.com/v1",
        new_subdomains=[],
        new_live_urls=[],
        new_technologies=[],
        technologies=[],
        screenshot_urls=[],
    )

    assert asset.score == 2
    assert asset.reasons == ["API keyword"]


def test_score_asset_adds_identity_category_bonus() -> None:
    asset = score_asset(
        "https://identity.example.com",
        new_subdomains=[],
        new_live_urls=[],
        new_technologies=[],
        technologies=["Keycloak"],
        screenshot_urls=[],
    )

    assert asset.score == 3
    assert asset.reasons == ["Identity technology"]


def test_prioritize_assets_sorts_by_score_then_url() -> None:
    assets = prioritize_assets(
        ["https://z.example.com", "https://admin.example.com", "https://api.example.com"],
        technology_fingerprints={"https://api.example.com": ["FastAPI"]},
        new_subdomains=["admin.example.com"],
        new_live_urls=["https://z.example.com"],
        new_technologies=["FastAPI"],
        screenshot_urls=["https://admin.example.com"],
    )

    assert [asset.url for asset in assets] == [
        "https://admin.example.com",
        "https://api.example.com",
        "https://z.example.com",
    ]
    assert [asset.score for asset in assets] == [9, 6, 5]


def test_summarize_priorities_counts_high_interest_assets() -> None:
    assets = prioritize_assets(
        ["https://plain.example.com", "https://api.example.com"],
        technology_fingerprints={},
        new_subdomains=[],
        new_live_urls=[],
        new_technologies=[],
        screenshot_urls=[],
    )

    assert summarize_priorities(assets) == {"total": 2, "high_interest": 1}
