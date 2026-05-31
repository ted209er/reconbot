"""Passive reconnaissance scan profile settings."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TypeVar


class ScanProfile(StrEnum):
    """Supported passive reconnaissance profiles."""

    LIGHT = "light"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass(frozen=True, slots=True)
class ProfileToolSettings:
    """Tool settings that can be adjusted by a scan profile."""

    enabled: bool
    binary: str
    timeout: float


SettingsT = TypeVar("SettingsT", bound=ProfileToolSettings)
LIGHT_TOOLS = frozenset({"subfinder", "httpx", "gau"})
PROFILE_TIMEOUT_SECONDS = {
    ScanProfile.LIGHT: {"default": 60.0},
    ScanProfile.DEEP: {"default": 300.0, "screenshots": 600.0},
}


def apply_profile(
    settings: dict[str, SettingsT],
    profile: ScanProfile,
) -> dict[str, SettingsT]:
    """Apply a passive scan profile to existing tool settings."""
    if profile == ScanProfile.STANDARD:
        return dict(settings)
    if profile == ScanProfile.LIGHT:
        return {
            name: replace(
                tool_settings,
                enabled=tool_settings.enabled and name in LIGHT_TOOLS,
                timeout=min(tool_settings.timeout, _profile_timeout(profile, name)),
            )
            for name, tool_settings in settings.items()
        }
    return {
        name: replace(
            tool_settings,
            enabled=True,
            timeout=max(tool_settings.timeout, _profile_timeout(profile, name)),
        )
        for name, tool_settings in settings.items()
    }


def _profile_timeout(profile: ScanProfile, tool_name: str) -> float:
    """Return the configured timeout bound for a tool profile."""
    timeouts = PROFILE_TIMEOUT_SECONDS[profile]
    return timeouts.get(tool_name, timeouts["default"])
