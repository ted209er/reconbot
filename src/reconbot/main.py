"""Reconbot application entry point."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from urllib.parse import urlparse

from reconbot.cli import parse_args
from reconbot.collection_status import (
    CollectionState,
    CollectionStatus,
    RunCompleteness,
    determine_run_completeness,
    disabled_status,
)
from reconbot.config import Config, get_bool, get_float, get_path, get_section, get_str, load_config
from reconbot.config_loader import get_default_config_path, load_default_config
from reconbot.doctor import HealthStatus, format_doctor_output, overall_status, run_doctor
from reconbot.exporting import build_json_export, write_json_export
from reconbot.fingerprinting import PassiveAssetMetadata, fingerprint_urls, summarize_technologies
from reconbot.guidance import build_investigation_plan, summarize_guidance
from reconbot.history import (
    DEFAULT_DATABASE_PATH,
    calculate_added_items,
    calculate_added_screenshots,
    calculate_added_technologies,
    calculate_removed_items,
    calculate_removed_screenshots,
    calculate_removed_technologies,
    get_previous_live_urls,
    get_previous_screenshots,
    get_previous_subdomains,
    get_previous_technologies,
    initialize_database,
    record_collection_statuses,
    record_historical_url_intelligence,
    record_live_urls,
    record_run,
    record_screenshot_diagnostics,
    record_screenshots,
    record_subdomains,
    record_technologies,
)
from reconbot.logging_config import setup_logging
from reconbot.models import ReconReport, ReconTarget, ToolResult
from reconbot.planning import PlanningError, generate_review_dossier
from reconbot.prioritization import prioritize_assets
from reconbot.profiles import ProfileToolSettings, ScanProfile, apply_profile
from reconbot.reporting import write_markdown_report
from reconbot.screenshots import ScreenshotDiagnostic, capture_screenshots
from reconbot.technology_categories import (
    categorize_assets,
    categorize_technologies,
    summarize_asset_categories,
    summarize_categories,
)
from reconbot.tools.assetfinder import find_subdomains as find_assetfinder_subdomains
from reconbot.tools.crtsh import find_subdomains as find_crtsh_subdomains
from reconbot.tools.detection import MissingExternalToolsError, validate_required_tools
from reconbot.tools.gau import find_urls as find_historical_urls
from reconbot.tools.httpx import find_live_urls
from reconbot.tools.subfinder import find_subdomains
from reconbot.tools.waybackurls import find_urls as find_wayback_urls
from reconbot.url_intelligence import (
    classify_historical_urls,
    summarize_historical_urls,
    write_historical_url_tsv,
)
from reconbot.utils.normalize import safe_filename
from reconbot.workspaces import WorkspacePaths, ensure_workspace, resolve_workspace

REQUIRED_EXTERNAL_TOOLS = (
    "subfinder",
    "assetfinder",
    "crtsh",
    "httpx",
    "gau",
    "waybackurls",
    "screenshots",
)
DEFAULT_TOOL_BINARIES = {"crtsh": "curl", "screenshots": "gowitness"}
DEFAULT_TOOL_TIMEOUTS = {"screenshots": 300.0}
HISTORY_DATABASE_PATH = DEFAULT_DATABASE_PATH


ToolSettings = ProfileToolSettings


def run_workflow(
    domain: str,
    config_path: Path | None,
    verbose: bool,
    run_name: str = "",
    workspace_path: Path | None = None,
    profile: ScanProfile = ScanProfile.STANDARD,
) -> ReconReport:
    """Run the recon orchestration workflow."""
    config, effective_config_path, using_packaged_config = _load_runtime_config(config_path)
    logging_section = get_section(config, "logging")
    output_section = get_section(config, "output")
    tool_settings = apply_profile(_load_tool_settings(get_section(config, "tools")), profile)
    workspace = _prepare_workspace(workspace_path)
    log_file = get_path(logging_section, "file", Path("logs/reconbot.log"))
    processed_dir = (
        workspace.processed_dir
        if workspace is not None
        else get_path(output_section, "processed_dir", Path("data/processed"))
    )
    reports_dir = (
        workspace.reports_dir
        if workspace is not None
        else get_path(output_section, "reports_dir", Path("reports"))
    )
    screenshots_root = (
        workspace.screenshots_dir
        if workspace is not None
        else get_path(output_section, "screenshots_dir", reports_dir / "screenshots")
    )
    json_exports_dir = (
        workspace.json_exports_dir
        if workspace is not None
        else get_path(output_section, "json_exports_dir", Path("reports/json"))
    )
    database_path = workspace.database_path if workspace is not None else HISTORY_DATABASE_PATH
    write_json = get_bool(output_section, "write_json", True)
    logger = setup_logging(verbose=verbose, log_file=log_file)

    target = ReconTarget(domain=domain, config_path=effective_config_path)
    report = ReconReport(target=target)
    collection_statuses: list[CollectionStatus] = []
    screenshot_diagnostics: list[ScreenshotDiagnostic] = []

    _print_startup_banner(
        target.domain,
        effective_config_path,
        run_name,
        workspace,
        using_packaged_config,
        profile,
    )
    _print_tool_settings(tool_settings)
    logger.info("Starting recon workflow for %s", target.domain)
    if using_packaged_config:
        logger.info("Using packaged default config")
    else:
        logger.info("Using config: %s", target.config_path)
    logger.debug("Loaded configuration from %s", target.config_path)
    logger.info("Initializing run history database at %s", database_path)
    initialize_database(database_path)
    logger.info("Checking external tool availability")
    validate_required_tools(_enabled_binaries(tool_settings))

    _print_stage("Subdomain discovery")
    subdomain_sources = _discover_subdomains(
        target.domain,
        tool_settings,
        logger,
        collection_statuses,
    )
    subdomains = _dedupe_sorted(subdomain_sources.values())
    _record_result(report, "subfinder", subdomains)
    subdomains_path = processed_dir / "subdomains.txt"
    _write_lines(subdomains_path, subdomains)

    httpx_settings = tool_settings["httpx"]
    if httpx_settings.enabled:
        _print_stage("Live host detection")
        logger.info("Running live host detection")
        live_urls = find_live_urls(
            subdomains,
            binary=httpx_settings.binary,
            timeout=httpx_settings.timeout,
            collection_statuses=collection_statuses,
        )
        if not subdomains:
            collection_statuses.append(
                CollectionStatus(
                    source="httpx",
                    target=target.domain,
                    status=CollectionState.ZERO_RESULTS,
                    result_count=0,
                )
            )
    else:
        logger.info("Skipping live host detection because httpx is disabled")
        collection_statuses.append(disabled_status(source="httpx", target=target.domain))
        live_urls = []
    _record_result(report, "httpx", live_urls)
    live_urls_path = processed_dir / "live_urls.txt"
    _write_lines(live_urls_path, live_urls)

    if httpx_settings.enabled:
        _print_stage("Technology fingerprinting")
        logger.info("Running technology fingerprinting")
        passive_metadata: dict[str, PassiveAssetMetadata] = {}
        technology_fingerprints = fingerprint_urls(
            live_urls,
            binary=httpx_settings.binary,
            timeout=httpx_settings.timeout,
            metadata=passive_metadata,
        )
    else:
        logger.info("Skipping technology fingerprinting because httpx is disabled")
        passive_metadata = {}
        technology_fingerprints = {}
    technology_summary = summarize_technologies(technology_fingerprints)
    technology_categories = categorize_technologies(technology_summary)
    technology_category_summary = summarize_categories(technology_categories)
    asset_categories = categorize_assets(
        technology_fingerprints,
        response_headers={
            url: metadata.response_headers for url, metadata in passive_metadata.items()
        },
        page_titles={url: metadata.title for url, metadata in passive_metadata.items()},
        platform_indicators={
            url: metadata.platform_indicators for url, metadata in passive_metadata.items()
        },
    )
    asset_category_summary = summarize_asset_categories(asset_categories)
    technologies_path = processed_dir / "technologies.txt"
    _write_lines(technologies_path, _format_technology_lines(technology_fingerprints))

    screenshot_settings = tool_settings["screenshots"]
    screenshots_dir = screenshots_root / safe_filename(target.domain)
    if screenshot_settings.enabled:
        _print_stage("Screenshot capture")
        logger.info("Running screenshot capture")
        screenshots = capture_screenshots(
            live_urls,
            output_dir=screenshots_dir,
            binary=screenshot_settings.binary,
            timeout=screenshot_settings.timeout,
            collection_statuses=collection_statuses,
            diagnostics=screenshot_diagnostics,
        )
        if not live_urls:
            collection_statuses.append(
                CollectionStatus(
                    source="gowitness",
                    target=target.domain,
                    status=CollectionState.ZERO_RESULTS,
                    result_count=0,
                )
            )
    else:
        logger.info("Skipping screenshot capture because screenshots are disabled")
        collection_statuses.append(disabled_status(source="gowitness", target=target.domain))
        screenshots = {}

    _print_stage("Historical URL collection")
    historical_targets: str | list[str] = _hosts_from_urls(live_urls) or target.domain
    historical_url_sources = _discover_historical_urls(
        historical_targets,
        tool_settings,
        logger,
        collection_statuses,
    )
    historical_urls = _dedupe_sorted(historical_url_sources.values())
    _record_result(report, "gau", historical_urls)
    historical_urls_path = processed_dir / "historical_urls.txt"
    _write_lines(historical_urls_path, historical_urls)
    historical_url_intelligence = classify_historical_urls(historical_url_sources)
    historical_url_summary = summarize_historical_urls(historical_url_intelligence)
    historical_url_intelligence_path = processed_dir / "historical-urls-classified.tsv"
    write_historical_url_tsv(historical_url_intelligence, historical_url_intelligence_path)

    logger.info(
        "Recon summary for %s: %s subdomains, %s live URLs, %s historical URLs",
        target.domain,
        len(subdomains),
        len(live_urls),
        len(historical_urls),
    )
    previous_subdomains = get_previous_subdomains(
        target=target.domain,
        database_path=database_path,
    )
    previous_live_urls = get_previous_live_urls(
        target=target.domain,
        database_path=database_path,
    )
    previous_technologies = get_previous_technologies(
        target=target.domain,
        database_path=database_path,
    )
    previous_screenshots = get_previous_screenshots(
        target=target.domain,
        database_path=database_path,
    )
    current_technologies = sorted(technology_summary)
    diff_items = {
        "added_subdomains": calculate_added_items(subdomains, previous_subdomains),
        "removed_subdomains": calculate_removed_items(subdomains, previous_subdomains),
        "added_live_urls": calculate_added_items(live_urls, previous_live_urls),
        "removed_live_urls": calculate_removed_items(live_urls, previous_live_urls),
    }
    technology_diff = {
        "added_technologies": calculate_added_technologies(
            current_technologies,
            previous_technologies,
        ),
        "removed_technologies": calculate_removed_technologies(
            current_technologies,
            previous_technologies,
        ),
    }
    screenshot_diff = {
        "added_screenshots": calculate_added_screenshots(screenshots, previous_screenshots),
        "removed_screenshots": calculate_removed_screenshots(screenshots, previous_screenshots),
    }
    prioritized_assets = prioritize_assets(
        live_urls,
        technology_fingerprints=technology_fingerprints,
        new_subdomains=diff_items["added_subdomains"],
        new_live_urls=diff_items["added_live_urls"],
        new_technologies=technology_diff["added_technologies"],
        screenshot_urls=list(screenshots),
    )
    investigation_guidance = build_investigation_plan(
        prioritized_assets,
        asset_categories=asset_categories,
        technology_fingerprints=technology_fingerprints,
        new_live_urls=diff_items["added_live_urls"],
        screenshot_urls=list(screenshots),
    )
    guidance_summary = summarize_guidance(investigation_guidance)
    run_status = determine_run_completeness(collection_statuses)
    report.complete()
    if report.finished_at is None:
        raise RuntimeError("report completion timestamp was not set")
    run_id = record_run(
        target=target.domain,
        run_name=run_name,
        started_at=report.started_at,
        completed_at=report.finished_at,
        subdomain_count=len(subdomains),
        live_url_count=len(live_urls),
        url_count=len(historical_urls),
        profile=profile.value,
        run_status=run_status.value,
        database_path=database_path,
    )
    record_subdomains(run_id=run_id, subdomains=subdomains, database_path=database_path)
    record_live_urls(run_id=run_id, urls=live_urls, database_path=database_path)
    record_technologies(
        run_id=run_id,
        technologies=technology_fingerprints,
        database_path=database_path,
    )
    record_screenshots(
        run_id=run_id,
        screenshots=screenshots,
        captured_at=report.finished_at,
        database_path=database_path,
    )
    record_screenshot_diagnostics(
        run_id=run_id,
        diagnostics=screenshot_diagnostics,
        database_path=database_path,
    )
    record_collection_statuses(
        run_id=run_id,
        statuses=collection_statuses,
        database_path=database_path,
    )
    record_historical_url_intelligence(
        run_id=run_id,
        findings=historical_url_intelligence,
        database_path=database_path,
    )
    output_files = {
        "subdomains": subdomains_path,
        "live_hosts": live_urls_path,
        "historical_urls": historical_urls_path,
        "historical_url_intelligence": historical_url_intelligence_path,
        "technologies": technologies_path,
        "screenshots": screenshots_dir,
    }
    report_path = reports_dir / f"{target.domain}.md"
    write_markdown_report(
        report,
        output_files,
        report_path,
        diff_items,
        technology_summary,
        technology_categories,
        technology_diff,
        run_name,
        screenshots,
        screenshot_diff,
        prioritized_assets,
        _source_counts(subdomain_sources),
        _source_counts(historical_url_sources),
        workspace.root if workspace is not None else None,
        profile.value,
        asset_categories,
        asset_category_summary,
        investigation_guidance,
        guidance_summary,
        collection_statuses,
        run_status,
        screenshot_settings.enabled,
        screenshot_diagnostics,
        historical_url_intelligence,
        historical_url_summary,
    )
    json_export_path = json_exports_dir / f"{safe_filename(target.domain)}.json"
    if write_json:
        json_export = build_json_export(
            report=report,
            run_name=run_name,
            output_files=output_files,
            report_path=report_path,
            subdomains=subdomains,
            live_urls=live_urls,
            historical_urls=historical_urls,
            technology_summary=technology_summary,
            technology_categories=technology_categories,
            technology_category_summary=technology_category_summary,
            technology_diff=technology_diff,
            screenshots=screenshots,
            screenshot_diff=screenshot_diff,
            prioritized_assets=prioritized_assets,
            subdomain_sources=_source_counts(subdomain_sources),
            historical_url_sources=_source_counts(historical_url_sources),
            workspace_path=workspace.root if workspace is not None else None,
            profile=profile.value,
            asset_categories=asset_categories,
            asset_category_summary=asset_category_summary,
            investigation_guidance=investigation_guidance,
            guidance_summary=guidance_summary,
            collection_statuses=collection_statuses,
            run_status=run_status,
            screenshot_diagnostics=screenshot_diagnostics,
            historical_url_intelligence=historical_url_intelligence,
            asset_diff=diff_items,
        )
        write_json_export(json_export, json_export_path)
        logger.info("Wrote JSON export to %s", json_export_path)
    else:
        logger.info("Skipping JSON export because output.write_json is false")
    logger.info("Wrote markdown report to %s", report_path)
    logger.info("Recon workflow complete for %s", target.domain)
    _print_completion(
        report_path=report_path,
        output_paths=[
            subdomains_path,
            live_urls_path,
            historical_urls_path,
            historical_url_intelligence_path,
            technologies_path,
            screenshots_dir,
            json_export_path,
        ],
        subdomain_count=len(subdomains),
        live_url_count=len(live_urls),
        historical_url_count=len(historical_urls),
        run_status=run_status,
    )
    return report


def _load_tool_settings(config: Config) -> dict[str, ToolSettings]:
    """Load external tool settings from config."""
    return {
        tool_name: _load_one_tool_settings(config, tool_name)
        for tool_name in REQUIRED_EXTERNAL_TOOLS
    }


def _load_one_tool_settings(config: Config, tool_name: str) -> ToolSettings:
    """Load settings for one external tool."""
    section = get_section(config, tool_name)
    return ToolSettings(
        enabled=get_bool(section, "enabled", True),
        binary=get_str(section, "binary", DEFAULT_TOOL_BINARIES.get(tool_name, tool_name)),
        timeout=get_float(section, "timeout", DEFAULT_TOOL_TIMEOUTS.get(tool_name, 120.0)),
    )


def _enabled_binaries(tool_settings: dict[str, ToolSettings]) -> list[str]:
    """Return binaries for enabled external tools."""
    return [settings.binary for settings in tool_settings.values() if settings.enabled]


def _prepare_workspace(workspace_path: Path | None) -> WorkspacePaths | None:
    """Resolve and create an optional workspace."""
    resolved = resolve_workspace(workspace_path)
    if resolved is None:
        return None
    return ensure_workspace(resolved)


def _load_runtime_config(config_path: Path | None) -> tuple[Config, Path, bool]:
    """Load custom config or packaged default config."""
    if config_path is None:
        return load_default_config(), get_default_config_path(), True
    return load_config(config_path), config_path, False


def _discover_subdomains(
    domain: str,
    tool_settings: dict[str, ToolSettings],
    logger: logging.Logger,
    collection_statuses: list[CollectionStatus],
) -> dict[str, list[str]]:
    """Run enabled passive subdomain sources."""
    results: dict[str, list[str]] = {}
    source_functions = {
        "subfinder": find_subdomains,
        "assetfinder": find_assetfinder_subdomains,
        "crtsh": find_crtsh_subdomains,
    }
    for source_name, source_function in source_functions.items():
        settings = tool_settings[source_name]
        if not settings.enabled:
            logger.info("Skipping %s because it is disabled", source_name)
            status_source = "crt.sh" if source_name == "crtsh" else source_name
            collection_statuses.append(disabled_status(source=status_source, target=domain))
            results[source_name] = []
            continue
        logger.info("Running %s subdomain discovery", source_name)
        results[source_name] = source_function(
            domain,
            binary=settings.binary,
            timeout=settings.timeout,
            collection_statuses=collection_statuses,
        )
    return results


def _discover_historical_urls(
    targets: str | list[str],
    tool_settings: dict[str, ToolSettings],
    logger: logging.Logger,
    collection_statuses: list[CollectionStatus],
) -> dict[str, list[str]]:
    """Run enabled passive historical URL sources."""
    results: dict[str, list[str]] = {}
    source_functions = {
        "gau": find_historical_urls,
        "waybackurls": find_wayback_urls,
    }
    for source_name, source_function in source_functions.items():
        settings = tool_settings[source_name]
        if not settings.enabled:
            logger.info("Skipping %s because it is disabled", source_name)
            collection_statuses.append(
                disabled_status(source=source_name, target=_status_target(targets))
            )
            results[source_name] = []
            continue
        logger.info("Running %s historical URL collection", source_name)
        results[source_name] = source_function(
            targets,
            binary=settings.binary,
            timeout=settings.timeout,
            collection_statuses=collection_statuses,
        )
    return results


def _dedupe_sorted(values: Iterable[list[str]]) -> list[str]:
    """Merge nested string lists into sorted unique values."""
    merged: set[str] = set()
    for value_list in values:
        merged.update(value_list)
    return sorted(merged)


def _source_counts(sources: dict[str, list[str]]) -> dict[str, int]:
    """Return deterministic per-source result counts."""
    return {source: len(values) for source, values in sorted(sources.items())}


def _print_startup_banner(
    domain: str,
    config_path: Path,
    run_name: str,
    workspace: WorkspacePaths | None,
    using_packaged_config: bool,
    profile: ScanProfile,
) -> None:
    """Print a concise startup banner."""
    print("Reconbot")
    print(f"Target: {domain}")
    print(f"Profile: {profile.value}")
    if run_name:
        print(f"Run name: {run_name}")
    if using_packaged_config:
        print("Using packaged default config")
    else:
        print("Using config:")
        print(f"  {config_path}")
    if workspace is not None:
        print(f"Workspace: {workspace.root}")


def _print_tool_settings(tool_settings: dict[str, ToolSettings]) -> None:
    """Print enabled tools and configured binaries."""
    print("Tools:")
    for name, settings in tool_settings.items():
        state = "enabled" if settings.enabled else "disabled"
        print(f"- {name}: {state}, binary={settings.binary}, timeout={settings.timeout:g}s")


def _print_stage(name: str) -> None:
    """Print workflow progress."""
    print(f"Running: {name}")


def _print_completion(
    *,
    report_path: Path,
    output_paths: list[Path],
    subdomain_count: int,
    live_url_count: int,
    historical_url_count: int,
    run_status: RunCompleteness,
) -> None:
    """Print concise completion details."""
    print("Complete")
    print(
        "Summary: "
        f"{subdomain_count} subdomains, "
        f"{live_url_count} live URLs, "
        f"{historical_url_count} historical URLs"
    )
    print(f"Run completeness: {run_status.value}")
    print(f"Report: {report_path}")
    print("Outputs:")
    for path in output_paths:
        print(f"- {path}")


def _record_result(report: ReconReport, name: str, values: list[str]) -> None:
    """Record workflow step output in the report."""
    report.add_result(
        ToolResult(
            name=name,
            success=True,
            output="\n".join(values),
        )
    )


def _write_lines(path: Path, values: list[str]) -> None:
    """Write newline-delimited output to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(values)
    path.write_text(f"{content}\n" if content else "", encoding="utf-8")


def _format_technology_lines(fingerprints: dict[str, list[str]]) -> list[str]:
    """Format technology fingerprints for processed output."""
    return [
        f"{url}\t{technology}"
        for url, technologies in sorted(fingerprints.items())
        for technology in sorted(technologies)
    ]


def _hosts_from_urls(urls: list[str]) -> list[str]:
    """Extract sorted unique hostnames from HTTP URLs."""
    hosts = {parsed.netloc for url in urls if (parsed := urlparse(url)).netloc}
    return sorted(hosts)


def _status_target(targets: str | list[str]) -> str:
    """Return a concise deterministic target label for disabled collectors."""
    if isinstance(targets, str):
        return targets
    return ", ".join(sorted(targets))


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the application."""
    args = parse_args(argv)
    if args.command == "doctor":
        results = run_doctor(workspace_path=args.workspace)
        print(format_doctor_output(results))
        status = overall_status(results)
        if status == HealthStatus.HEALTHY:
            return 0
        if status == HealthStatus.WARNINGS:
            return 1
        return 2
    if args.command == "plan":
        try:
            dossier_paths = generate_review_dossier(args.workspace)
        except PlanningError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        print("Investigation plan generated")
        print(f"- {dossier_paths.markdown}")
        print(f"- {dossier_paths.json}")
        return 0

    try:
        run_workflow(
            domain=args.domain,
            config_path=args.config,
            verbose=args.verbose,
            run_name=args.run_name,
            workspace_path=args.workspace,
            profile=ScanProfile(args.profile),
        )
    except FileNotFoundError:
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        return 2
    except MissingExternalToolsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        if args.verbose:
            logging.getLogger("reconbot").exception("Recon workflow failed")
        else:
            print(
                "Error: recon workflow failed. Re-run with --verbose for details.",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
