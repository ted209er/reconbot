from reconbot.profiles import ProfileToolSettings, ScanProfile, apply_profile


def _settings() -> dict[str, ProfileToolSettings]:
    return {
        "subfinder": ProfileToolSettings(True, "subfinder", 120),
        "assetfinder": ProfileToolSettings(True, "assetfinder", 120),
        "crtsh": ProfileToolSettings(True, "curl", 120),
        "httpx": ProfileToolSettings(True, "httpx", 120),
        "gau": ProfileToolSettings(True, "gau", 120),
        "waybackurls": ProfileToolSettings(True, "waybackurls", 120),
        "screenshots": ProfileToolSettings(True, "gowitness", 300),
    }


def test_standard_profile_preserves_tool_settings() -> None:
    settings = _settings()

    assert apply_profile(settings, ScanProfile.STANDARD) == settings


def test_light_profile_uses_core_passive_sources_and_shorter_timeouts() -> None:
    settings = apply_profile(_settings(), ScanProfile.LIGHT)

    assert settings["subfinder"].enabled is True
    assert settings["httpx"].enabled is True
    assert settings["gau"].enabled is True
    assert settings["assetfinder"].enabled is False
    assert settings["crtsh"].enabled is False
    assert settings["waybackurls"].enabled is False
    assert settings["screenshots"].enabled is False
    assert {tool.timeout for tool in settings.values()} == {60.0}


def test_light_profile_does_not_enable_disabled_core_tools() -> None:
    settings = _settings()
    settings["gau"] = ProfileToolSettings(False, "gau", 120)

    profiled = apply_profile(settings, ScanProfile.LIGHT)

    assert profiled["gau"].enabled is False


def test_deep_profile_enables_all_passive_sources_and_longer_timeouts() -> None:
    settings = {
        name: ProfileToolSettings(False, tool.binary, 30)
        for name, tool in _settings().items()
    }

    profiled = apply_profile(settings, ScanProfile.DEEP)

    assert all(tool.enabled for tool in profiled.values())
    assert profiled["subfinder"].timeout == 300.0
    assert profiled["screenshots"].timeout == 600.0
