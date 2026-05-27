"""Reconbot application entry point."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlparse

from reconbot.cli import parse_args
from reconbot.config import get_path, get_section, load_config
from reconbot.logging_config import setup_logging
from reconbot.models import ReconReport, ReconTarget, ToolResult
from reconbot.reporting import write_markdown_report
from reconbot.tools.detection import validate_required_tools
from reconbot.tools.gau import find_urls as find_historical_urls
from reconbot.tools.httpx import find_live_urls
from reconbot.tools.subfinder import find_subdomains

REQUIRED_EXTERNAL_TOOLS = ("subfinder", "httpx", "gau")


def run_workflow(domain: str, config_path: Path, verbose: bool) -> ReconReport:
    """Run the recon orchestration workflow."""
    config = load_config(config_path)
    logging_section = get_section(config, "logging")
    output_section = get_section(config, "output")
    log_file = get_path(logging_section, "file", Path("logs/reconbot.log"))
    processed_dir = get_path(output_section, "processed_dir", Path("data/processed"))
    reports_dir = get_path(output_section, "reports_dir", Path("reports"))
    logger = setup_logging(verbose=verbose, log_file=log_file)

    target = ReconTarget(domain=domain, config_path=config_path)
    report = ReconReport(target=target)

    logger.info("Starting recon workflow for %s", target.domain)
    logger.debug("Loaded configuration from %s", target.config_path)
    logger.info("Checking external tool availability")
    validate_required_tools(REQUIRED_EXTERNAL_TOOLS)

    logger.info("Running subdomain discovery")
    subdomains = find_subdomains(target.domain)
    _record_result(report, "subfinder", subdomains)
    subdomains_path = processed_dir / "subdomains.txt"
    _write_lines(subdomains_path, subdomains)

    logger.info("Running live host detection")
    live_urls = find_live_urls(subdomains)
    _record_result(report, "httpx", live_urls)
    live_urls_path = processed_dir / "live_urls.txt"
    _write_lines(live_urls_path, live_urls)

    logger.info("Running historical URL collection")
    historical_urls = find_historical_urls(_hosts_from_urls(live_urls))
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
    return report


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
    except Exception:
        logging.getLogger("reconbot").exception("Recon workflow failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
