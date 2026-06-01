"""Passive screenshot capture helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.models import ToolResult
from reconbot.tools.gowitness import run_screenshot_capture
from reconbot.utils.normalize import safe_filename
from reconbot.utils.subprocess_runner import TIMEOUT_RETURN_CODE

LOGGER = logging.getLogger(__name__)
DEFAULT_BINARY = "gowitness"
DEFAULT_TIMEOUT_SECONDS = 300.0


class ScreenshotStatus(StrEnum):
    """Supported per-URL screenshot outcomes."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    NO_ARTIFACT = "NO_ARTIFACT"


@dataclass(frozen=True, slots=True)
class ScreenshotDiagnostic:
    """One auditable per-URL screenshot collection result."""

    url: str
    status: ScreenshotStatus
    screenshot_path: Path | None
    return_code: int
    error: str = ""


def capture_screenshot(
    url: str,
    *,
    output_dir: Path,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    collection_statuses: list[CollectionStatus] | None = None,
    diagnostics: list[ScreenshotDiagnostic] | None = None,
) -> Path | None:
    """Capture one live URL screenshot with gowitness."""
    target = url.strip()
    if not target:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = output_dir / f"{safe_filename(target)}.png"
    result = run_screenshot_capture(
        target,
        output_dir=output_dir,
        binary=binary,
        timeout=timeout,
    )
    diagnostic = _build_diagnostic(target, screenshot_path, result)
    if diagnostics is not None:
        diagnostics.append(diagnostic)
    if collection_statuses is not None:
        collection_statuses.append(_collection_status(diagnostic))
    if diagnostic.status != ScreenshotStatus.SUCCESS:
        LOGGER.warning(
            "gowitness screenshot failed for %s: %s",
            target,
            diagnostic.error,
        )
        return None
    return screenshot_path


def capture_screenshots(
    urls: list[str],
    *,
    output_dir: Path,
    binary: str = DEFAULT_BINARY,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    collection_statuses: list[CollectionStatus] | None = None,
    diagnostics: list[ScreenshotDiagnostic] | None = None,
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
            collection_statuses=collection_statuses,
            diagnostics=diagnostics,
        )
        if screenshot_path is not None:
            screenshots[target] = screenshot_path
    return screenshots


def _build_diagnostic(
    url: str,
    screenshot_path: Path,
    result: ToolResult,
) -> ScreenshotDiagnostic:
    """Return a deterministic screenshot diagnostic from execution and artifact state."""
    if result.return_code == TIMEOUT_RETURN_CODE:
        return ScreenshotDiagnostic(
            url=url,
            status=ScreenshotStatus.TIMED_OUT,
            screenshot_path=None,
            return_code=result.return_code,
            error=_error_summary(result.error) or "gowitness screenshot capture timed out",
        )
    if not result.success:
        return ScreenshotDiagnostic(
            url=url,
            status=ScreenshotStatus.FAILED,
            screenshot_path=None,
            return_code=result.return_code,
            error=_error_summary(result.error)
            or f"gowitness exited with return code {result.return_code}",
        )
    if not screenshot_path.is_file():
        return ScreenshotDiagnostic(
            url=url,
            status=ScreenshotStatus.NO_ARTIFACT,
            screenshot_path=None,
            return_code=result.return_code,
            error=f"gowitness completed but screenshot artifact is missing: {screenshot_path}",
        )
    if screenshot_path.stat().st_size <= 0:
        return ScreenshotDiagnostic(
            url=url,
            status=ScreenshotStatus.NO_ARTIFACT,
            screenshot_path=None,
            return_code=result.return_code,
            error=f"gowitness completed but screenshot artifact is empty: {screenshot_path}",
        )
    return ScreenshotDiagnostic(
        url=url,
        status=ScreenshotStatus.SUCCESS,
        screenshot_path=screenshot_path,
        return_code=result.return_code,
    )


def _collection_status(diagnostic: ScreenshotDiagnostic) -> CollectionStatus:
    """Map screenshot diagnostics into shared collection-quality evidence."""
    if diagnostic.status == ScreenshotStatus.SUCCESS:
        state = CollectionState.SUCCESS
        result_count = 1
    elif diagnostic.status == ScreenshotStatus.TIMED_OUT:
        state = CollectionState.TIMED_OUT
        result_count = 0
    else:
        state = CollectionState.FAILED
        result_count = 0
    return CollectionStatus(
        source="gowitness",
        target=diagnostic.url,
        status=state,
        result_count=result_count,
        return_code=diagnostic.return_code,
        error_summary=diagnostic.error,
    )


def _error_summary(error: str, *, limit: int = 240) -> str:
    """Return concise single-line stderr for reports and JSON exports."""
    summary = " ".join(error.split())
    if len(summary) <= limit:
        return summary
    return summary[: limit - 3] + "..."
