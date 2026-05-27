"""YAML configuration loading and typed helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar, cast

import yaml

Config = dict[str, Any]
T = TypeVar("T")


def load_config(path: Path) -> Config:
    """Load a YAML configuration file from disk."""
    config_path = path.expanduser()
    with config_path.open("r", encoding="utf-8") as config_file:
        loaded = yaml.safe_load(config_file)

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Configuration must be a mapping: {config_path}")
    return cast(Config, loaded)


def get_section(config: Config, key: str) -> Config:
    """Return a nested configuration section as a dictionary."""
    value = config.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(f"Configuration key '{key}' must be a mapping.")
    return value


def get_value(config: Config, key: str, default: T) -> object | T:
    """Return a raw configuration value or the provided default."""
    value: object | T = config.get(key, default)
    return default if value is None else value


def get_str(config: Config, key: str, default: str) -> str:
    """Return a string configuration value."""
    value = get_value(config, key, default)
    if not isinstance(value, str):
        raise TypeError(f"Configuration key '{key}' must be a string.")
    return value


def get_bool(config: Config, key: str, default: bool) -> bool:
    """Return a boolean configuration value."""
    value = get_value(config, key, default)
    if not isinstance(value, bool):
        raise TypeError(f"Configuration key '{key}' must be a boolean.")
    return value


def get_int(config: Config, key: str, default: int) -> int:
    """Return an integer configuration value."""
    value = get_value(config, key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"Configuration key '{key}' must be an integer.")
    return value


def get_path(config: Config, key: str, default: Path) -> Path:
    """Return a pathlib.Path configuration value."""
    value = get_value(config, key, str(default))
    if isinstance(value, Path):
        return value
    if not isinstance(value, str):
        raise TypeError(f"Configuration key '{key}' must be a path string.")
    return Path(value)
