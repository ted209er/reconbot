from pathlib import Path

import pytest

from reconbot.config import get_bool, get_int, get_path, get_section, get_str, load_config


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "logging:\n  file: logs/test.log\nfeatures:\n  enabled: true\n  limit: 3\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    logging_config = get_section(config, "logging")
    features_config = get_section(config, "features")
    assert get_path(logging_config, "file", Path("logs/default.log")) == Path("logs/test.log")
    assert get_bool(features_config, "enabled", False) is True
    assert get_int(features_config, "limit", 1) == 3


def test_load_config_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("- item\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        load_config(config_path)


def test_get_str_rejects_wrong_type() -> None:
    with pytest.raises(TypeError, match="string"):
        get_str({"domain": 10}, "domain", "example.com")
