"""Plain markdown report generation."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from reconbot.models import ReconReport


def write_markdown_report(
    report: ReconReport,
    output_files: Mapping[str, Path],
    report_path: Path,
    diff_items: Mapping[str, list[str]] | None = None,
) -> Path:
    """Write a plain markdown report to disk."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown_report(report, output_files, diff_items)
    report_path.write_text(markdown, encoding="utf-8")
    return report_path


def build_markdown_report(
    report: ReconReport,
    output_files: Mapping[str, Path],
    diff_items: Mapping[str, list[str]] | None = None,
) -> str:
    """Build a plain markdown report for a recon run."""
    lines = [
        "# Reconbot Report",
        "",
        f"- Target domain: `{report.target.domain}`",
        f"- Run timestamp: `{report.started_at.isoformat()}`",
        f"- Subdomain count: {_result_count(report, 'subfinder')}",
        f"- Live host count: {_result_count(report, 'httpx')}",
        f"- URL count: {_result_count(report, 'gau')}",
        "",
    ]
    if diff_items is not None:
        lines.extend(_build_diff_section(diff_items))
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Subdomains: `{output_files['subdomains']}`",
            f"- Live hosts: `{output_files['live_hosts']}`",
            f"- Historical URLs: `{output_files['historical_urls']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_diff_section(diff_items: Mapping[str, list[str]]) -> list[str]:
    """Build markdown lines for current-vs-previous run changes."""
    added_subdomains = diff_items.get("added_subdomains", [])
    removed_subdomains = diff_items.get("removed_subdomains", [])
    added_live_urls = diff_items.get("added_live_urls", [])
    removed_live_urls = diff_items.get("removed_live_urls", [])
    lines = [
        "## Changes Since Previous Run",
        "",
        f"- Added subdomains: {len(added_subdomains)}",
        f"- Removed subdomains: {len(removed_subdomains)}",
        f"- Added live URLs: {len(added_live_urls)}",
        f"- Removed live URLs: {len(removed_live_urls)}",
        "",
    ]
    lines.extend(_format_changed_items("+", added_subdomains))
    lines.extend(_format_changed_items("-", removed_subdomains))
    lines.extend(_format_changed_items("+", added_live_urls))
    lines.extend(_format_changed_items("-", removed_live_urls))
    lines.append("")
    return lines


def _format_changed_items(prefix: str, values: list[str]) -> list[str]:
    """Format changed values as simple markdown lines."""
    return [f"{prefix} {value}" for value in values]


def _result_count(report: ReconReport, name: str) -> int:
    """Count newline-delimited values in a recorded tool result."""
    for result in report.results:
        if result.name == name:
            return len([line for line in result.output.splitlines() if line.strip()])
    return 0
