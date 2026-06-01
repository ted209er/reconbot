"""Plain markdown report generation."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from reconbot.collection_status import CollectionStatus, RunCompleteness
from reconbot.guidance import AssetGuidance
from reconbot.models import ReconReport
from reconbot.prioritization import PrioritizedAsset
from reconbot.screenshots import ScreenshotDiagnostic, ScreenshotStatus
from reconbot.technology_categories import (
    ASSET_CATEGORY_ORDER,
    CATEGORY_ORDER,
    AssetCategory,
)
from reconbot.url_intelligence import (
    HISTORICAL_OBSERVATION_TYPE,
    HISTORICAL_REACHABILITY,
    HistoricalUrlFinding,
    top_historical_leads,
)


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
    workspace_path: Path | None = None,
    profile: str = "standard",
    asset_categories: Mapping[str, list[AssetCategory]] | None = None,
    asset_category_summary: Mapping[str, int] | None = None,
    investigation_guidance: list[AssetGuidance] | None = None,
    guidance_summary: Mapping[str, int] | None = None,
    collection_statuses: list[CollectionStatus] | None = None,
    run_status: RunCompleteness = RunCompleteness.COMPLETE,
    screenshots_enabled: bool = False,
    screenshot_diagnostics: list[ScreenshotDiagnostic] | None = None,
    historical_url_intelligence: list[HistoricalUrlFinding] | None = None,
    historical_url_summary: Mapping[str, int] | None = None,
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
        workspace_path,
        profile,
        asset_categories,
        asset_category_summary,
        investigation_guidance,
        guidance_summary,
        collection_statuses,
        run_status,
        screenshots_enabled,
        screenshot_diagnostics,
        historical_url_intelligence,
        historical_url_summary,
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
    workspace_path: Path | None = None,
    profile: str = "standard",
    asset_categories: Mapping[str, list[AssetCategory]] | None = None,
    asset_category_summary: Mapping[str, int] | None = None,
    investigation_guidance: list[AssetGuidance] | None = None,
    guidance_summary: Mapping[str, int] | None = None,
    collection_statuses: list[CollectionStatus] | None = None,
    run_status: RunCompleteness = RunCompleteness.COMPLETE,
    screenshots_enabled: bool = False,
    screenshot_diagnostics: list[ScreenshotDiagnostic] | None = None,
    historical_url_intelligence: list[HistoricalUrlFinding] | None = None,
    historical_url_summary: Mapping[str, int] | None = None,
) -> str:
    """Build a plain markdown report for a recon run."""
    lines = [
        "# Reconbot Report",
        "",
        f"- Target domain: `{report.target.domain}`",
        f"- Run name: `{run_name or 'default'}`",
        f"- Profile: `{profile}`",
        f"- Run completeness: `{run_status.value}`",
        f"- Execution timestamp: `{report.started_at.isoformat()}`",
        f"- Subdomain count: {_result_count(report, 'subfinder')}",
        f"- Live host count: {_result_count(report, 'httpx')}",
        f"- URL count: {_result_count(report, 'gau')}",
        "",
    ]
    if workspace_path is not None:
        lines.extend(["Workspace:", "", f"    {workspace_path}", ""])
    if collection_statuses is not None:
        lines.extend(_build_collection_quality_section(collection_statuses, run_status))
    if diff_items is not None:
        lines.extend(_build_diff_section(diff_items))
    if technology_summary is not None:
        lines.extend(_build_technology_summary_section(technology_summary))
    if technology_categories is not None:
        lines.extend(_build_technology_categories_section(technology_categories))
    if asset_categories is not None:
        lines.extend(_build_asset_categories_section(asset_categories, asset_category_summary))
    if technology_diff is not None:
        lines.extend(_build_technology_changes_section(technology_diff))
    if screenshots is not None:
        lines.extend(
            _build_screenshot_section(
                screenshots,
                screenshot_diff,
                enabled=screenshots_enabled,
                diagnostics=screenshot_diagnostics,
            )
        )
    if prioritized_assets is not None:
        lines.extend(_build_prioritized_asset_section(prioritized_assets))
    if investigation_guidance is not None:
        lines.extend(
            _build_investigation_guidance_section(investigation_guidance, guidance_summary)
        )
    if historical_url_intelligence is not None:
        lines.extend(
            _build_historical_url_intelligence_section(
                historical_url_intelligence,
                historical_url_summary,
            )
        )
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


def _build_collection_quality_section(
    statuses: list[CollectionStatus],
    run_status: RunCompleteness,
) -> list[str]:
    """Build human-readable collection quality evidence."""
    lines = ["## Collection Quality", "", f"- Run completeness: {run_status.value}", ""]
    if not statuses:
        lines.extend(["- No collection status evidence recorded", ""])
        return lines

    for status in sorted(statuses, key=lambda item: (item.source, item.target, item.status.value)):
        details = [
            f"status={status.status.value}",
            f"results={status.result_count}",
        ]
        if status.return_code is not None:
            details.append(f"return_code={status.return_code}")
        lines.append(f"- {status.source} [{status.target}]: " + ", ".join(details))
        if status.error_summary:
            lines.append(f"  Error: {status.error_summary}")
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
    if "historical_url_intelligence" in output_files:
        lines.append(
            "- Classified historical URLs: "
            f"`{output_files['historical_url_intelligence']}`"
        )
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


def _build_asset_categories_section(
    asset_categories: Mapping[str, list[AssetCategory]],
    category_summary: Mapping[str, int] | None,
) -> list[str]:
    """Build category-sorted passive asset classification lines."""
    lines = ["## Asset Categories", "", "Category Summary:", ""]
    summary = category_summary or {}
    if summary:
        for category in ASSET_CATEGORY_ORDER:
            if count := summary.get(category):
                lines.append(f"- {category}: {count} assets")
    else:
        lines.append("- None detected")
    lines.append("")

    for category in ASSET_CATEGORY_ORDER:
        categorized_urls = [
            (url, match)
            for url, matches in sorted(asset_categories.items())
            for match in matches
            if match.category == category
        ]
        if not categorized_urls:
            continue
        lines.extend([f"{category}:", ""])
        for url, match in categorized_urls:
            lines.append(f"- {url} ({match.confidence.value} confidence)")
        lines.append("")
    return lines


def _build_screenshot_section(
    screenshots: Mapping[str, Path],
    screenshot_diff: Mapping[str, list[str]] | None,
    *,
    enabled: bool,
    diagnostics: list[ScreenshotDiagnostic] | None,
) -> list[str]:
    """Build markdown lines for captured screenshots."""
    added = screenshot_diff.get("added_screenshots", []) if screenshot_diff else []
    removed = screenshot_diff.get("removed_screenshots", []) if screenshot_diff else []
    diagnostic_items = diagnostics or []
    failures = [
        diagnostic
        for diagnostic in diagnostic_items
        if diagnostic.status != ScreenshotStatus.SUCCESS
    ]
    lines = [
        "## Screenshots",
        "",
        "Screenshot Summary:",
        "",
        f"- Screenshot collection enabled: {'yes' if enabled else 'no'}",
        f"- Screenshots captured: {len(screenshots)}",
        f"- Screenshot failures: {len(failures)}/{len(diagnostic_items)} assets failed",
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
    if failures:
        lines.append("Screenshot warnings:")
        lines.append("")
        for diagnostic in sorted(failures, key=lambda item: item.url):
            lines.append(f"- {diagnostic.url}: {diagnostic.status.value} - {diagnostic.error}")
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


def _build_investigation_guidance_section(
    guidance: list[AssetGuidance],
    guidance_summary: Mapping[str, int] | None,
) -> list[str]:
    """Build safe manual investigation guidance lines."""
    lines = ["## Suggested Manual Investigation Plan", ""]
    if not guidance:
        lines.extend(["- No live assets available for manual review.", ""])
        return lines

    if guidance_summary:
        lines.extend(["Check Summary:", ""])
        for category, count in sorted(guidance_summary.items()):
            lines.append(f"- {category}: {count} checks")
        lines.append("")

    for asset in guidance:
        lines.extend([f"### {asset.url}", ""])
        for reason in asset.reasons:
            lines.append(f"- Evidence: {reason}")
        lines.append("")
        for check in asset.checks:
            lines.extend(
                [
                    f"#### {check.category}: {check.title}",
                    "",
                    f"- Why it matters: {check.why_it_matters}",
                    f"- Safe manual approach: {check.safe_manual_approach}",
                    f"- Evidence to collect: {check.evidence_to_collect}",
                    f"- Safety note: {check.safety_note}",
                    "",
                ]
            )
    return lines


def _build_historical_url_intelligence_section(
    findings: list[HistoricalUrlFinding],
    summary: Mapping[str, int] | None,
) -> list[str]:
    """Build a concise report view of passive historical URL intelligence."""
    lines = [
        "## Historical URL Intelligence",
        "",
        f"- Classification: {HISTORICAL_OBSERVATION_TYPE}",
        f"- Reachability: {HISTORICAL_REACHABILITY}",
        "- These URLs are passive historical leads, not current observations or evidence "
        "that an archived URL remains reachable.",
        "",
        "Category Summary:",
        "",
    ]
    if summary:
        for category, count in summary.items():
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- None identified")
    lines.extend(["", "Top Historical Leads:", ""])
    leads = top_historical_leads(findings)
    if not leads:
        lines.extend(["- None identified", ""])
        return lines
    for index, finding in enumerate(leads, start=1):
        lines.extend(
            [
                f"{index}. {finding.url}",
                f"   - Categories: {', '.join(finding.categories)}",
                f"   - Sources: {', '.join(finding.sources)}",
                f"   - Confidence: {finding.confidence.value}",
                f"   - Reason: {'; '.join(finding.reasons)}",
                "",
            ]
        )
    return lines


def _result_count(report: ReconReport, name: str) -> int:
    """Count newline-delimited values in a recorded tool result."""
    for result in report.results:
        if result.name == name:
            return len([line for line in result.output.splitlines() if line.strip()])
    return 0
