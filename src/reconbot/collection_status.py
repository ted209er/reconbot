"""Typed collection quality evidence for passive reconnaissance sources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from reconbot.models import ToolResult
from reconbot.utils.subprocess_runner import TIMEOUT_RETURN_CODE


class CollectionState(StrEnum):
    """Supported collection result states."""

    SUCCESS = "SUCCESS"
    ZERO_RESULTS = "ZERO_RESULTS"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    DISABLED = "DISABLED"


class RunCompleteness(StrEnum):
    """Overall run completeness derived from enabled collection sources."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class CollectionStatus:
    """One human-readable passive collection source result."""

    source: str
    target: str
    status: CollectionState
    result_count: int
    return_code: int | None = None
    error_summary: str = ""


def status_from_result(
    *,
    source: str,
    target: str,
    result: ToolResult,
    result_count: int,
) -> CollectionStatus:
    """Build a collection status from one external tool result."""
    if result.return_code == TIMEOUT_RETURN_CODE:
        state = CollectionState.TIMED_OUT
    elif not result.success:
        state = CollectionState.FAILED
    elif result_count == 0:
        state = CollectionState.ZERO_RESULTS
    else:
        state = CollectionState.SUCCESS
    return CollectionStatus(
        source=source,
        target=target,
        status=state,
        result_count=result_count,
        return_code=result.return_code,
        error_summary=_summarize_error(result.error),
    )


def disabled_status(*, source: str, target: str) -> CollectionStatus:
    """Build a disabled collection source status."""
    return CollectionStatus(
        source=source,
        target=target,
        status=CollectionState.DISABLED,
        result_count=0,
    )


def determine_run_completeness(statuses: list[CollectionStatus]) -> RunCompleteness:
    """Return overall run completeness from enabled collection statuses."""
    enabled = [status for status in statuses if status.status != CollectionState.DISABLED]
    if not enabled:
        return RunCompleteness.COMPLETE
    failures = [
        status
        for status in enabled
        if status.status in {CollectionState.FAILED, CollectionState.TIMED_OUT}
    ]
    if not failures:
        return RunCompleteness.COMPLETE
    if len(failures) == len(enabled):
        return RunCompleteness.FAILED
    return RunCompleteness.PARTIAL


def _summarize_error(error: str, *, limit: int = 240) -> str:
    """Return a concise single-line error suitable for reports and history."""
    summary = " ".join(error.split())
    if len(summary) <= limit:
        return summary
    return summary[: limit - 3] + "..."
