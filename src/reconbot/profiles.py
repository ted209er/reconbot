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
LIGHT_TIMEOUT_SECONDS = 60.0
DEEP_TIMEOUT_SECONDS = 300.0
DEEP_SCREENSHOT_TIMEOUT_SECONDS = 600.0


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
                timeout=min(tool_settings.timeout, LIGHT_TIMEOUT_SECONDS),
            )
            for name, tool_settings in settings.items()
        }
    return {
        name: replace(
            tool_settings,
            enabled=True,
            timeout=max(
                tool_settings.timeout,
                (
                    DEEP_SCREENSHOT_TIMEOUT_SECONDS
                    if name == "screenshots"
                    else DEEP_TIMEOUT_SECONDS
                ),
            ),
        )
        for name, tool_settings in settings.items()
    }
