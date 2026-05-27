"""Reconbot application entry point."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from reconbot.cli import parse_args
from reconbot.config import get_path, get_section, load_config
from reconbot.logging_config import setup_logging
from reconbot.models import ReconReport, ReconTarget


def run_workflow(domain: str, config_path: Path, verbose: bool) -> ReconReport:
    """Run the placeholder orchestration workflow."""
    config = load_config(config_path)
    logging_section = get_section(config, "logging")
    log_file = get_path(logging_section, "file", Path("logs/reconbot.log"))
    logger = setup_logging(verbose=verbose, log_file=log_file)

    target = ReconTarget(domain=domain, config_path=config_path)
    report = ReconReport(target=target)

    logger.info("Starting recon workflow for %s", target.domain)
    logger.debug("Loaded configuration from %s", target.config_path)
    logger.info("Preparing target context")
    logger.info("No recon integrations are enabled in the foundation build")
    report.complete()
    logger.info("Recon workflow complete for %s", target.domain)
    return report


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
