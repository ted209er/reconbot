from pathlib import Path

from reconbot.cli import parse_args


def test_parse_args_accepts_domain_config_and_verbose() -> None:
    args = parse_args(["--domain", "example.com", "--config", "config.yaml", "--verbose"])

    assert args.domain == "example.com"
    assert args.config == Path("config.yaml")
    assert args.verbose is True


def test_parse_args_uses_default_config() -> None:
    args = parse_args(["--domain", "example.com"])

    assert args.config == Path("configs/default.yaml")
    assert args.verbose is False
