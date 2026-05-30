"""Packaged default configuration loading."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from reconbot.config import Config, load_config

DEFAULT_CONFIG_RESOURCE = "configs/default.yaml"


def get_default_config_path() -> Path:
    """Return the installed packaged default config path."""
    resource = resources.files("reconbot").joinpath(DEFAULT_CONFIG_RESOURCE)
    with resources.as_file(resource) as path:
        return path


def load_default_config() -> Config:
    """Load the packaged default configuration."""
    return load_config(get_default_config_path())
