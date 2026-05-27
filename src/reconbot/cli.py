"""Command-line parsing for Reconbot."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("configs/default.yaml")


def build_parser() -> argparse.ArgumentParser:
    """Build the Reconbot command-line parser."""
    parser = argparse.ArgumentParser(
        prog="reconbot",
        description="Run authorized reconnaissance workflow placeholders.",
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Authorized target domain to prepare for reconnaissance.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
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
