"""External tool availability checks."""

from __future__ import annotations

from collections.abc import Iterable
from shutil import which


class MissingExternalToolsError(RuntimeError):
    """Raised when required external binaries are not available."""


def find_missing_tools(tool_names: Iterable[str]) -> list[str]:
    """Return required tool names that are not available on PATH."""
    return sorted({tool_name for tool_name in tool_names if which(tool_name) is None})


def validate_required_tools(tool_names: Iterable[str]) -> None:
    """Raise a clear error if required external binaries are missing."""
    missing_tools = find_missing_tools(tool_names)
    if not missing_tools:
        return

    missing = ", ".join(missing_tools)
    raise MissingExternalToolsError(
        f"Missing required external tool(s): {missing}. "
        "Install them separately and ensure they are available on PATH."
    )
