"""Lightweight wrapper for the gowitness CLI."""

from __future__ import annotations

from pathlib import Path

from reconbot.models import ToolResult
from reconbot.utils.subprocess_runner import run_command

DEFAULT_BINARY = "gowitness"
DEFAULT_TIMEOUT_SECONDS = 300.0


def run_screenshot_capture(
    target: str,
    *,
    output_dir: Path,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> ToolResult:
    """Run one gowitness screenshot capture."""
    return run_command(
        "gowitness",
        [
            binary,
            "scan",
            "single",
            "--url",
            target,
            "--screenshot-path",
            str(output_dir),
        ],
        timeout=timeout,
    )


def run_basic_check(
    *,
    binary: str = DEFAULT_BINARY,
    timeout: float = 10.0,
) -> ToolResult:
    """Run a local-only gowitness version check."""
    return run_command(
        "gowitness",
        [binary, "version"],
        timeout=timeout,
    )
