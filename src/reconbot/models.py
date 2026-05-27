"""Core Reconbot data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class ReconTarget:
    """Authorized target metadata for a recon workflow."""

    domain: str
    config_path: Path


@dataclass(slots=True)
class ToolResult:
    """Result from a future recon tool execution."""

    name: str
    success: bool
    command: list[str] = field(default_factory=list)
    output: str = ""
    error: str = ""
    return_code: int = 0


@dataclass(slots=True)
class ReconReport:
    """Aggregate report for a recon workflow."""

    target: ReconTarget
    results: list[ToolResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    def add_result(self, result: ToolResult) -> None:
        """Add a tool result to the report."""
        self.results.append(result)

    def complete(self) -> None:
        """Mark the report as complete."""
        self.finished_at = datetime.now(UTC)

    @property
    def successful(self) -> bool:
        """Return whether every recorded result succeeded."""
        return all(result.success for result in self.results)
