from pathlib import Path

import pytest

from reconbot.cli import parse_args


def test_parse_args_accepts_domain_config_verbose_and_run_name(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("logging:\n  file: logs/test.log\n", encoding="utf-8")

    args = parse_args(
        [
            "--domain",
            "example.com",
            "--config",
            str(config_path),
            "--verbose",
            "--run-name",
            "daily",
            "--workspace",
            str(tmp_path / "workspace"),
        ]
    )

    assert args.domain == "example.com"
    assert args.config == config_path
    assert args.verbose is True
    assert args.run_name == "daily"
    assert args.workspace == tmp_path / "workspace"


def test_parse_args_uses_default_config() -> None:
    args = parse_args(["--domain", "example.com"])

    assert args.config is None
    assert args.verbose is False
    assert args.run_name == ""
    assert args.workspace is None


def test_parse_args_rejects_invalid_domain() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--domain", "https://example.com/path"])


def test_parse_args_rejects_missing_config() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--domain", "example.com", "--config", "missing.yaml"])


def test_parse_args_accepts_doctor_workspace(tmp_path: Path) -> None:
    args = parse_args(["doctor", "--workspace", str(tmp_path / "workspace")])

    assert args.command == "doctor"
    assert args.workspace == tmp_path / "workspace"
