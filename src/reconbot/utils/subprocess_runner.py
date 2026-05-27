"""Safe subprocess execution helpers."""

from __future__ import annotations

import logging
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from reconbot.models import ToolResult

LOGGER = logging.getLogger(__name__)
TIMEOUT_RETURN_CODE = -1
MISSING_EXECUTABLE_RETURN_CODE = 127


def run_command(
    name: str,
    command: Sequence[str],
    *,
    timeout: float | None = None,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ToolResult:
    """Run a command safely and return a structured result."""
    command_parts = list(command)
    LOGGER.info("Starting command '%s': %s", name, command_parts)

    try:
        completed = subprocess.run(
            command_parts,
            capture_output=True,
            check=False,
            cwd=cwd,
            env=_build_environment(env),
            shell=False,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output = _normalize_output(exc.stdout)
        error = _normalize_output(exc.stderr) or f"Command timed out after {timeout} seconds."
        LOGGER.warning("Command '%s' timed out after %s seconds", name, timeout)
        return ToolResult(
            name=name,
            success=False,
            command=command_parts,
            output=output,
            error=error,
            return_code=TIMEOUT_RETURN_CODE,
        )
    except FileNotFoundError as exc:
        LOGGER.error("Command '%s' failed: executable not found", name)
        return ToolResult(
            name=name,
            success=False,
            command=command_parts,
            error=str(exc),
            return_code=MISSING_EXECUTABLE_RETURN_CODE,
        )

    success = completed.returncode == 0
    if success:
        LOGGER.info("Command '%s' completed successfully", name)
    else:
        LOGGER.warning("Command '%s' exited with code %s", name, completed.returncode)

    return ToolResult(
        name=name,
        success=success,
        command=command_parts,
        output=completed.stdout,
        error=completed.stderr,
        return_code=completed.returncode,
    )


def _normalize_output(value: bytes | str | None) -> str:
    """Convert subprocess timeout output into text."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _build_environment(env: Mapping[str, str] | None) -> dict[str, str] | None:
    """Merge command-specific environment variables with the current process environment."""
    if env is None:
        return None
    return {**os.environ, **env}
