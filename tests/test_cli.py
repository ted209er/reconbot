from pathlib import Path

import pytest

from reconbot.cli import parse_args


def test_parse_args_accepts_domain_config_and_verbose(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("logging:\n  file: logs/test.log\n", encoding="utf-8")

    args = parse_args(["--domain", "example.com", "--config", str(config_path), "--verbose"])

    assert args.domain == "example.com"
    assert args.config == config_path
    assert args.verbose is True


def test_parse_args_uses_default_config() -> None:
    args = parse_args(["--domain", "example.com"])

    assert args.config == Path("configs/default.yaml")
    assert args.verbose is False


def test_parse_args_rejects_invalid_domain() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--domain", "https://example.com/path"])


def test_parse_args_rejects_missing_config() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--domain", "example.com", "--config", "missing.yaml"])
