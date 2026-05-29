"""Command-line parsing for Reconbot."""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("configs/default.yaml")
DOMAIN_PATTERN = re.compile(r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$")


def build_parser() -> argparse.ArgumentParser:
    """Build the Reconbot command-line parser."""
    parser = argparse.ArgumentParser(
        prog="reconbot",
        description="Run authorized reconnaissance workflow placeholders.",
    )
    parser.add_argument(
        "--domain",
        type=_domain,
        required=True,
        metavar="DOMAIN",
        help="Authorized target domain, for example example.com.",
    )
    parser.add_argument(
        "--config",
        type=_config_path,
        default=DEFAULT_CONFIG_PATH,
        metavar="PATH",
        help=f"Path to YAML configuration file. Defaults to {DEFAULT_CONFIG_PATH}.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose console logging.",
    )
    return parser


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    return build_parser().parse_args(args)


def _domain(value: str) -> str:
    """Validate and normalize a CLI domain value."""
    domain = value.strip().lower().rstrip(".")
    if "://" in domain or "/" in domain or not DOMAIN_PATTERN.fullmatch(domain):
        raise argparse.ArgumentTypeError(
            "domain must be a hostname like example.com, without a scheme or path"
        )
    return domain


def _config_path(value: str) -> Path:
    """Validate a CLI config path."""
    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"config file not found: {path}")
    return path
