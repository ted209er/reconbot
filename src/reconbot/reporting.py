"""Plain markdown report generation."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from reconbot.models import ReconReport


def write_markdown_report(
    report: ReconReport,
    output_files: Mapping[str, Path],
    report_path: Path,
) -> Path:
    """Write a plain markdown report to disk."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_markdown_report(report, output_files), encoding="utf-8")
    return report_path


def build_markdown_report(report: ReconReport, output_files: Mapping[str, Path]) -> str:
    """Build a plain markdown report for a recon run."""
    return "\n".join(
        [
            "# Reconbot Report",
            "",
            f"- Target domain: `{report.target.domain}`",
            f"- Run timestamp: `{report.started_at.isoformat()}`",
            f"- Subdomain count: {_result_count(report, 'subfinder')}",
            f"- Live host count: {_result_count(report, 'httpx')}",
            f"- URL count: {_result_count(report, 'gau')}",
            "",
            "## Output Files",
            "",
            f"- Subdomains: `{output_files['subdomains']}`",
            f"- Live hosts: `{output_files['live_hosts']}`",
            f"- Historical URLs: `{output_files['historical_urls']}`",
            "",
        ]
    )


def _result_count(report: ReconReport, name: str) -> int:
    """Count newline-delimited values in a recorded tool result."""
    for result in report.results:
        if result.name == name:
            return len([line for line in result.output.splitlines() if line.strip()])
    return 0
