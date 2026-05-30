"""Workspace path helpers for engagement-specific recon data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WorkspacePaths:
    """Resolved artifact paths for one Reconbot workspace."""

    root: Path
    data_dir: Path
    processed_dir: Path
    reports_dir: Path
    screenshots_dir: Path
    findings_dir: Path
    notes_dir: Path
    scope_file: Path
    database_path: Path
    json_exports_dir: Path


def resolve_workspace(path: Path | str | None) -> Path | None:
    """Resolve an optional workspace path without creating it."""
    if path is None:
        return None
    return Path(path).expanduser().resolve()


def workspace_paths(workspace: Path) -> WorkspacePaths:
    """Return deterministic artifact paths for a resolved workspace."""
    root = workspace.expanduser().resolve()
    data_dir = root / "data"
    reports_dir = root / "reports"
    screenshots_dir = root / "screenshots"
    return WorkspacePaths(
        root=root,
        data_dir=data_dir,
        processed_dir=data_dir / "processed",
        reports_dir=reports_dir,
        screenshots_dir=screenshots_dir,
        findings_dir=root / "findings",
        notes_dir=root / "notes",
        scope_file=root / "scope.txt",
        database_path=data_dir / "reconbot.db",
        json_exports_dir=reports_dir / "json",
    )


def ensure_workspace(workspace: Path) -> WorkspacePaths:
    """Create the standard workspace layout and return its paths."""
    paths = workspace_paths(workspace)
    for directory in (
        paths.data_dir,
        paths.reports_dir,
        paths.screenshots_dir,
        paths.findings_dir,
        paths.notes_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    paths.scope_file.touch(exist_ok=True)
    return paths
