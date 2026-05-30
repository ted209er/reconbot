"""Plain markdown report generation."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from reconbot.models import ReconReport
from reconbot.prioritization import PrioritizedAsset
from reconbot.technology_categories import CATEGORY_ORDER


def write_markdown_report(
    report: ReconReport,
    output_files: Mapping[str, Path],
    report_path: Path,
    diff_items: Mapping[str, list[str]] | None = None,
    technology_summary: Mapping[str, int] | None = None,
    technology_categories: Mapping[str, Mapping[str, int]] | None = None,
    technology_diff: Mapping[str, list[str]] | None = None,
    run_name: str = "",
    screenshots: Mapping[str, Path] | None = None,
    screenshot_diff: Mapping[str, list[str]] | None = None,
    prioritized_assets: list[PrioritizedAsset] | None = None,
    subdomain_sources: Mapping[str, int] | None = None,
    historical_url_sources: Mapping[str, int] | None = None,
) -> Path:
    """Write a plain markdown report to disk."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown_report(
        report,
        output_files,
        diff_items,
        technology_summary,
        technology_categories,
        technology_diff,
        run_name,
        screenshots,
        screenshot_diff,
        prioritized_assets,
        subdomain_sources,
        historical_url_sources,
    )
    report_path.write_text(markdown, encoding="utf-8")
    return report_path


def build_markdown_report(
    report: ReconReport,
    output_files: Mapping[str, Path],
    diff_items: Mapping[str, list[str]] | None = None,
    technology_summary: Mapping[str, int] | None = None,
    technology_categories: Mapping[str, Mapping[str, int]] | None = None,
    technology_diff: Mapping[str, list[str]] | None = None,
    run_name: str = "",
    screenshots: Mapping[str, Path] | None = None,
    screenshot_diff: Mapping[str, list[str]] | None = None,
    prioritized_assets: list[PrioritizedAsset] | None = None,
    subdomain_sources: Mapping[str, int] | None = None,
    historical_url_sources: Mapping[str, int] | None = None,
) -> str:
    """Build a plain markdown report for a recon run."""
    lines = [
        "# Reconbot Report",
        "",
        f"- Target domain: `{report.target.domain}`",
        f"- Run name: `{run_name or 'default'}`",
        f"- Execution timestamp: `{report.started_at.isoformat()}`",
        f"- Subdomain count: {_result_count(report, 'subfinder')}",
        f"- Live host count: {_result_count(report, 'httpx')}",
        f"- URL count: {_result_count(report, 'gau')}",
        "",
    ]
    if diff_items is not None:
        lines.extend(_build_diff_section(diff_items))
    if technology_summary is not None:
        lines.extend(_build_technology_summary_section(technology_summary))
    if technology_categories is not None:
        lines.extend(_build_technology_categories_section(technology_categories))
    if technology_diff is not None:
        lines.extend(_build_technology_changes_section(technology_diff))
    if screenshots is not None:
        lines.extend(_build_screenshot_section(screenshots, screenshot_diff))
    if prioritized_assets is not None:
        lines.extend(_build_prioritized_asset_section(prioritized_assets))
    if subdomain_sources is not None or historical_url_sources is not None:
        lines.extend(_build_discovery_sources_section(subdomain_sources, historical_url_sources))
    lines.extend(_build_output_file_section(output_files))
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


def _build_output_file_section(output_files: Mapping[str, Path]) -> list[str]:
    """Build markdown lines for generated output files."""
    lines = [
        "## Output Files",
        "",
        f"- Subdomains: `{output_files['subdomains']}`",
        f"- Live hosts: `{output_files['live_hosts']}`",
        f"- Historical URLs: `{output_files['historical_urls']}`",
    ]
    if "technologies" in output_files:
        lines.append(f"- Technologies: `{output_files['technologies']}`")
    if "screenshots" in output_files:
        lines.append(f"- Screenshots: `{output_files['screenshots']}`")
    lines.append("")
    return lines


def _build_technology_summary_section(technology_summary: Mapping[str, int]) -> list[str]:
    """Build markdown lines for technology fingerprints."""
    lines = ["## Technology Summary", "", "Technologies:", ""]
    if technology_summary:
        for technology, count in sorted(technology_summary.items()):
            lines.append(f"- {technology} ({count})")
    else:
        lines.append("- None detected")
    lines.append("")
    return lines


def _build_technology_categories_section(
    technology_categories: Mapping[str, Mapping[str, int]],
) -> list[str]:
    """Build markdown lines for categorized technology fingerprints."""
    lines = ["## Technology Categories", ""]
    if not technology_categories:
        lines.extend(["- None detected", ""])
        return lines

    for category in CATEGORY_ORDER:
        technologies = technology_categories.get(category)
        if not technologies:
            continue
        lines.append(f"{category}:")
        lines.append("")
        for technology, count in sorted(technologies.items()):
            lines.append(f"- {technology} ({count})")
        lines.append("")
    extra_categories = sorted(
        category
        for category in technology_categories
        if category not in CATEGORY_ORDER and technology_categories[category]
    )
    for category in extra_categories:
        lines.append(f"{category}:")
        lines.append("")
        for technology, count in sorted(technology_categories[category].items()):
            lines.append(f"- {technology} ({count})")
        lines.append("")
    return lines


def _build_technology_changes_section(technology_diff: Mapping[str, list[str]]) -> list[str]:
    """Build markdown lines for technology changes."""
    added = technology_diff.get("added_technologies", [])
    removed = technology_diff.get("removed_technologies", [])
    lines = [
        "## Technology Changes",
        "",
        f"- Added technologies: {len(added)}",
        f"- Removed technologies: {len(removed)}",
        "",
    ]
    lines.extend(_format_changed_items("+", added))
    lines.extend(_format_changed_items("-", removed))
    lines.append("")
    return lines


def _build_screenshot_section(
    screenshots: Mapping[str, Path],
    screenshot_diff: Mapping[str, list[str]] | None,
) -> list[str]:
    """Build markdown lines for captured screenshots."""
    added = screenshot_diff.get("added_screenshots", []) if screenshot_diff else []
    removed = screenshot_diff.get("removed_screenshots", []) if screenshot_diff else []
    lines = [
        "## Screenshots",
        "",
        "Screenshot Summary:",
        "",
        f"- Screenshots captured: {len(screenshots)}",
        f"- New screenshot targets: {len(added)}",
        f"- Removed screenshot targets: {len(removed)}",
        "",
    ]
    if screenshots:
        lines.append("Screenshots:")
        lines.append("")
        for path in sorted(str(path) for path in screenshots.values()):
            lines.append(f"- {path}")
        lines.append("")
    if screenshot_diff is not None:
        lines.append("New screenshot targets:")
        lines.append("")
        lines.extend(_format_changed_items("+", added))
        lines.append("")
        lines.append("Removed screenshot targets:")
        lines.append("")
        lines.extend(_format_changed_items("-", removed))
        lines.append("")
    return lines


def _build_prioritized_asset_section(assets: list[PrioritizedAsset]) -> list[str]:
    """Build markdown lines for high interest assets."""
    high_interest_assets = [asset for asset in assets if asset.score > 0]
    lines = ["## High Interest Assets", ""]
    if not high_interest_assets:
        lines.extend(["- None identified", ""])
        return lines

    for index, asset in enumerate(high_interest_assets, start=1):
        lines.append(f"{index}. {asset.url}")
        lines.append("")
        lines.append(f"   Score: {asset.score}")
        lines.append("")
        lines.append("   Reasons:")
        lines.append("")
        for reason in asset.reasons:
            lines.append(f"   - {reason}")
        lines.append("")
    return lines


def _build_discovery_sources_section(
    subdomain_sources: Mapping[str, int] | None,
    historical_url_sources: Mapping[str, int] | None,
) -> list[str]:
    """Build markdown lines for passive source result counts."""
    lines = ["## Discovery Sources Summary", ""]
    if subdomain_sources is not None:
        lines.extend(["Subdomains:", ""])
        for source, count in sorted(subdomain_sources.items()):
            lines.append(f"- {source}: {count}")
        lines.append("")
    if historical_url_sources is not None:
        lines.extend(["Historical URLs:", ""])
        for source, count in sorted(historical_url_sources.items()):
            lines.append(f"- {source}: {count}")
        lines.append("")
    return lines


def _result_count(report: ReconReport, name: str) -> int:
    """Count newline-delimited values in a recorded tool result."""
    for result in report.results:
        if result.name == name:
            return len([line for line in result.output.splitlines() if line.strip()])
    return 0
