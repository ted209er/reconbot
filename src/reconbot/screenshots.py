"""Passive screenshot capture helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from reconbot.utils.normalize import safe_filename
from reconbot.utils.subprocess_runner import run_command

LOGGER = logging.getLogger(__name__)
DEFAULT_BINARY = "gowitness"
DEFAULT_TIMEOUT_SECONDS = 300.0


def capture_screenshot(
    url: str,
    *,
    output_dir: Path,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Path | None:
    """Capture one live URL screenshot with gowitness."""
    target = url.strip()
    if not target:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = output_dir / f"{safe_filename(target)}.png"
    result = run_command(
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
    if not result.success:
        LOGGER.warning("gowitness failed for %s with code %s", target, result.return_code)
        return None
    return screenshot_path


def capture_screenshots(
    urls: list[str],
    *,
    output_dir: Path,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Path]:
    """Capture screenshots for live URLs and return paths keyed by URL."""
    screenshots: dict[str, Path] = {}
    for url in urls:
        target = url.strip()
        if not target:
            continue
        screenshot_path = capture_screenshot(
            target,
            output_dir=output_dir,
            binary=binary,
            timeout=timeout,
        )
        if screenshot_path is not None:
            screenshots[target] = screenshot_path
    return screenshots
