import tomllib
from pathlib import Path

import pytest

from reconbot.config import (
    get_bool,
    get_float,
    get_int,
    get_path,
    get_section,
    get_str,
    load_config,
)
from reconbot.config_loader import get_default_config_path, load_default_config


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
    assert get_float(features_config, "limit", 1.0) == 3.0


def test_load_config_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("- item\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        load_config(config_path)


def test_load_default_config_reads_packaged_yaml() -> None:
    config = load_default_config()

    assert get_path(get_section(config, "logging"), "file", Path()) == Path("logs/reconbot.log")
    assert get_str(get_section(get_section(config, "tools"), "subfinder"), "binary", "") == (
        "subfinder"
    )


def test_get_default_config_path_points_to_packaged_file() -> None:
    default_config_path = get_default_config_path()

    assert default_config_path.name == "default.yaml"
    assert default_config_path.is_file()


def test_pyproject_packages_default_config() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    package_data = pyproject["tool"]["setuptools"]["package-data"]
    assert package_data["reconbot"] == ["configs/default.yaml"]


def test_get_str_rejects_wrong_type() -> None:
    with pytest.raises(TypeError, match="string"):
        get_str({"domain": 10}, "domain", "example.com")
