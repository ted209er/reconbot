"""Environment health checks for Reconbot."""

from __future__ import annotations

import sqlite3
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from shutil import which

from reconbot.config_loader import get_default_config_path, load_default_config
from reconbot.tools.gowitness import run_basic_check
from reconbot.workspaces import workspace_paths

REQUIRED_TOOL_BINARIES = (
    "subfinder",
    "assetfinder",
    "httpx",
    "gau",
    "waybackurls",
    "gowitness",
)
BROWSER_BINARIES = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "chrome",
)


class HealthStatus(IntEnum):
    """Ordered health status values."""

    HEALTHY = 0
    WARNINGS = 1
    ERROR = 2


@dataclass(frozen=True, slots=True)
class CheckResult:
    """One doctor check result."""

    name: str
    status: HealthStatus
    message: str


def check_python() -> CheckResult:
    """Check the active Python runtime version."""
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"
    if version >= (3, 11):
        return CheckResult("Python", HealthStatus.HEALTHY, f"Python {version_text}")
    return CheckResult(
        "Python",
        HealthStatus.ERROR,
        f"Python {version_text}; Reconbot requires Python 3.11 or newer",
    )


def check_config() -> CheckResult:
    """Check the packaged default config is available and loadable."""
    try:
        config_path = get_default_config_path()
        load_default_config()
    except Exception as exc:
        return CheckResult(
            "Config",
            HealthStatus.ERROR,
            f"Packaged default config is not loadable: {exc}",
        )
    if not config_path.is_file():
        return CheckResult(
            "Config",
            HealthStatus.ERROR,
            f"Packaged default config is missing: {config_path}",
        )
    return CheckResult("Config", HealthStatus.HEALTHY, f"Packaged default config: {config_path}")


def check_workspace(workspace_path: Path | None) -> CheckResult:
    """Check optional workspace structure without creating it."""
    if workspace_path is None:
        return CheckResult("Workspace", HealthStatus.HEALTHY, "No workspace requested")

    paths = workspace_paths(workspace_path)
    if paths.root.exists() and not paths.root.is_dir():
        return CheckResult(
            "Workspace",
            HealthStatus.ERROR,
            f"Workspace path is not a directory: {paths.root}",
        )
    if not paths.root.exists():
        return CheckResult(
            "Workspace",
            HealthStatus.WARNINGS,
            f"Workspace does not exist yet: {paths.root}",
        )

    missing: list[Path] = [
        path
        for path in (
            paths.data_dir,
            paths.reports_dir,
            paths.screenshots_dir,
            paths.findings_dir,
            paths.notes_dir,
            paths.scope_file,
        )
        if not path.exists()
    ]
    if missing:
        missing_names = ", ".join(str(path.relative_to(paths.root)) for path in missing)
        return CheckResult(
            "Workspace",
            HealthStatus.WARNINGS,
            f"Workspace is missing expected path(s): {missing_names}",
        )
    return CheckResult("Workspace", HealthStatus.HEALTHY, f"Workspace structure: {paths.root}")


def check_tools(tool_names: Iterable[str] = REQUIRED_TOOL_BINARIES) -> CheckResult:
    """Check external recon tool binaries are visible on PATH."""
    missing = sorted({tool_name for tool_name in tool_names if which(tool_name) is None})
    if missing:
        return CheckResult(
            "Tools",
            HealthStatus.WARNINGS,
            "Missing tool(s) on PATH: " + ", ".join(missing),
        )
    return CheckResult("Tools", HealthStatus.HEALTHY, "All supported tools found on PATH")


def check_sqlite() -> CheckResult:
    """Check SQLite is available in the Python standard library."""
    try:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as exc:
        return CheckResult("SQLite", HealthStatus.ERROR, f"SQLite check failed: {exc}")
    return CheckResult("SQLite", HealthStatus.HEALTHY, f"SQLite {sqlite3.sqlite_version}")


def check_gowitness() -> CheckResult:
    """Check local gowitness executable visibility and basic command execution."""
    executable = which("gowitness")
    if executable is None:
        return CheckResult(
            "gowitness",
            HealthStatus.WARNINGS,
            "gowitness executable is missing from PATH",
        )
    result = run_basic_check(binary=executable)
    if not result.success:
        error = " ".join(result.error.split()) or f"return code {result.return_code}"
        return CheckResult(
            "gowitness",
            HealthStatus.WARNINGS,
            f"gowitness version check failed: {error}",
        )
    return CheckResult("gowitness", HealthStatus.HEALTHY, f"gowitness executable: {executable}")


def check_browser() -> CheckResult:
    """Check local browser availability for gowitness screenshots."""
    for browser in BROWSER_BINARIES:
        if executable := which(browser):
            return CheckResult("Browser", HealthStatus.HEALTHY, f"Screenshot browser: {executable}")
    return CheckResult(
        "Browser",
        HealthStatus.WARNINGS,
        "Screenshot browser not found on PATH; install Chrome or Chromium",
    )


def run_doctor(workspace_path: Path | None = None) -> list[CheckResult]:
    """Run all environment checks."""
    return [
        check_python(),
        check_config(),
        check_sqlite(),
        check_workspace(workspace_path),
        check_tools(),
        check_gowitness(),
        check_browser(),
    ]


def overall_status(results: Iterable[CheckResult]) -> HealthStatus:
    """Return the most severe status from check results."""
    return max((result.status for result in results), default=HealthStatus.HEALTHY)


def format_doctor_output(results: Iterable[CheckResult]) -> str:
    """Format doctor results for humans."""
    result_list = list(results)
    lines = ["Reconbot Doctor", ""]
    for result in result_list:
        lines.append(f"[{result.status.name}] {result.name}: {result.message}")
    lines.extend(["", f"Result: {overall_status(result_list).name}"])
    return "\n".join(lines)
