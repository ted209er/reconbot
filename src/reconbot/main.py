"""Reconbot application entry point."""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from reconbot.cli import parse_args
from reconbot.config import Config, get_bool, get_float, get_path, get_section, get_str, load_config
from reconbot.history import DEFAULT_DATABASE_PATH, initialize_database, record_run
from reconbot.logging_config import setup_logging
from reconbot.models import ReconReport, ReconTarget, ToolResult
from reconbot.reporting import write_markdown_report
from reconbot.tools.detection import MissingExternalToolsError, validate_required_tools
from reconbot.tools.gau import find_urls as find_historical_urls
from reconbot.tools.httpx import find_live_urls
from reconbot.tools.subfinder import find_subdomains

REQUIRED_EXTERNAL_TOOLS = ("subfinder", "httpx", "gau")
HISTORY_DATABASE_PATH = DEFAULT_DATABASE_PATH


@dataclass(frozen=True, slots=True)
class ToolSettings:
    """Runtime settings for one external tool."""

    enabled: bool
    binary: str
    timeout: float


def run_workflow(domain: str, config_path: Path, verbose: bool) -> ReconReport:
    """Run the recon orchestration workflow."""
    config = load_config(config_path)
    logging_section = get_section(config, "logging")
    output_section = get_section(config, "output")
    tool_settings = _load_tool_settings(get_section(config, "tools"))
    log_file = get_path(logging_section, "file", Path("logs/reconbot.log"))
    processed_dir = get_path(output_section, "processed_dir", Path("data/processed"))
    reports_dir = get_path(output_section, "reports_dir", Path("reports"))
    logger = setup_logging(verbose=verbose, log_file=log_file)

    target = ReconTarget(domain=domain, config_path=config_path)
    report = ReconReport(target=target)

    _print_startup_banner(target.domain, config_path)
    _print_tool_settings(tool_settings)
    logger.info("Starting recon workflow for %s", target.domain)
    logger.debug("Loaded configuration from %s", target.config_path)
    logger.info("Initializing run history database at %s", HISTORY_DATABASE_PATH)
    initialize_database(HISTORY_DATABASE_PATH)
    logger.info("Checking external tool availability")
    validate_required_tools(_enabled_binaries(tool_settings))

    subfinder_settings = tool_settings["subfinder"]
    if subfinder_settings.enabled:
        _print_stage("Subdomain discovery")
        logger.info("Running subdomain discovery")
        subdomains = find_subdomains(
            target.domain,
            binary=subfinder_settings.binary,
            timeout=subfinder_settings.timeout,
        )
    else:
        logger.info("Skipping subdomain discovery because subfinder is disabled")
        subdomains = []
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
        )
    else:
        logger.info("Skipping live host detection because httpx is disabled")
        live_urls = []
    _record_result(report, "httpx", live_urls)
    live_urls_path = processed_dir / "live_urls.txt"
    _write_lines(live_urls_path, live_urls)

    gau_settings = tool_settings["gau"]
    if gau_settings.enabled:
        _print_stage("Historical URL collection")
        logger.info("Running historical URL collection")
        historical_targets: str | list[str] = _hosts_from_urls(live_urls) or target.domain
        historical_urls = find_historical_urls(
            historical_targets,
            binary=gau_settings.binary,
            timeout=gau_settings.timeout,
        )
    else:
        logger.info("Skipping historical URL collection because gau is disabled")
        historical_urls = []
    _record_result(report, "gau", historical_urls)
    historical_urls_path = processed_dir / "historical_urls.txt"
    _write_lines(historical_urls_path, historical_urls)

    logger.info(
        "Recon summary for %s: %s subdomains, %s live URLs, %s historical URLs",
        target.domain,
        len(subdomains),
        len(live_urls),
        len(historical_urls),
    )
    report.complete()
    if report.finished_at is None:
        raise RuntimeError("report completion timestamp was not set")
    record_run(
        target=target.domain,
        started_at=report.started_at,
        completed_at=report.finished_at,
        subdomain_count=len(subdomains),
        live_url_count=len(live_urls),
        url_count=len(historical_urls),
        database_path=HISTORY_DATABASE_PATH,
    )
    report_path = reports_dir / f"{target.domain}.md"
    write_markdown_report(
        report,
        {
            "subdomains": subdomains_path,
            "live_hosts": live_urls_path,
            "historical_urls": historical_urls_path,
        },
        report_path,
    )
    logger.info("Wrote markdown report to %s", report_path)
    logger.info("Recon workflow complete for %s", target.domain)
    _print_completion(
        report_path=report_path,
        output_paths=[subdomains_path, live_urls_path, historical_urls_path],
        subdomain_count=len(subdomains),
        live_url_count=len(live_urls),
        historical_url_count=len(historical_urls),
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
        binary=get_str(section, "binary", tool_name),
        timeout=get_float(section, "timeout", 120.0),
    )


def _enabled_binaries(tool_settings: dict[str, ToolSettings]) -> list[str]:
    """Return binaries for enabled external tools."""
    return [settings.binary for settings in tool_settings.values() if settings.enabled]


def _print_startup_banner(domain: str, config_path: Path) -> None:
    """Print a concise startup banner."""
    print("Reconbot")
    print(f"Target: {domain}")
    print(f"Config: {config_path}")


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
) -> None:
    """Print concise completion details."""
    print("Complete")
    print(
        "Summary: "
        f"{subdomain_count} subdomains, "
        f"{live_url_count} live URLs, "
        f"{historical_url_count} historical URLs"
    )
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


def _hosts_from_urls(urls: list[str]) -> list[str]:
    """Extract sorted unique hostnames from HTTP URLs."""
    hosts = {parsed.netloc for url in urls if (parsed := urlparse(url)).netloc}
    return sorted(hosts)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the application."""
    args = parse_args(argv)

    try:
        run_workflow(
            domain=args.domain,
            config_path=args.config,
            verbose=args.verbose,
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
