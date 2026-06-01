"""Command-line parsing for Reconbot."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from reconbot.profiles import ScanProfile

DOMAIN_PATTERN = re.compile(r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$")


def build_parser() -> argparse.ArgumentParser:
    """Build the Reconbot command-line parser."""
    if _is_doctor_command():
        return build_doctor_parser()
    if _is_plan_command():
        return build_plan_parser()
    return build_run_parser()


def build_run_parser() -> argparse.ArgumentParser:
    """Build the normal recon workflow parser."""
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
        default=None,
        metavar="PATH",
        help="Optional. Uses packaged default config if omitted.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose console logging.",
    )
    parser.add_argument(
        "--run-name",
        default="",
        metavar="NAME",
        help="Optional label stored with this run, for example daily or weekly-baseline.",
    )
    parser.add_argument(
        "--workspace",
        type=_workspace_path,
        default=None,
        metavar="PATH",
        help="Optional engagement workspace for generated data, reports, and run history.",
    )
    parser.add_argument(
        "--profile",
        choices=[profile.value for profile in ScanProfile],
        default=ScanProfile.STANDARD.value,
        help="Passive recon profile. Defaults to standard.",
    )
    return parser


def build_doctor_parser() -> argparse.ArgumentParser:
    """Build the doctor command parser."""
    parser = argparse.ArgumentParser(
        prog="reconbot doctor",
        description="Check Reconbot environment health without running recon.",
    )
    parser.set_defaults(command="doctor")
    parser.add_argument(
        "--workspace",
        type=_workspace_path,
        default=None,
        metavar="PATH",
        help="Optional engagement workspace to verify.",
    )
    return parser


def build_plan_parser() -> argparse.ArgumentParser:
    """Build the local-only investigation planning command parser."""
    parser = argparse.ArgumentParser(
        prog="reconbot plan",
        description="Build a local-only investigation dossier from workspace artifacts.",
    )
    parser.set_defaults(command="plan")
    parser.add_argument(
        "--workspace",
        type=_workspace_path,
        required=True,
        metavar="PATH",
        help="Existing engagement workspace containing Reconbot artifacts.",
    )
    return parser


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    argv = list(args) if args is not None else sys.argv[1:]
    if argv and argv[0] == "doctor":
        return build_doctor_parser().parse_args(argv[1:])
    if argv and argv[0] == "plan":
        return build_plan_parser().parse_args(argv[1:])
    parsed = build_run_parser().parse_args(argv)
    parsed.command = "run"
    return parsed


def _is_doctor_command() -> bool:
    """Return true when process argv is invoking the doctor command."""
    return len(sys.argv) > 1 and sys.argv[1] == "doctor"


def _is_plan_command() -> bool:
    """Return true when process argv is invoking the plan command."""
    return len(sys.argv) > 1 and sys.argv[1] == "plan"


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


def _workspace_path(value: str) -> Path:
    """Parse a workspace path that may not exist yet."""
    return Path(value).expanduser()
