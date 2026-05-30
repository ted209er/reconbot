# Changelog

All notable changes to Reconbot will be documented in this file.

Reconbot uses simple semantic versioning:

- `MAJOR`: breaking changes
- `MINOR`: new features
- `PATCH`: fixes and small improvements

## [Unreleased]

### Changed

- Expanded installation and onboarding documentation with the full supported
  external tool list, feature-to-tool mapping, verification commands, first-run
  steps, workspace usage, and troubleshooting guidance.
- Added optional workspace support for separating application code from
  engagement data, including workspace artifact paths, report metadata, JSON
  metadata, and workspace-specific SQLite run history.
- Added packaged default configuration loading so installed Reconbot can run
  without a repo-local `--config` path while preserving custom config overrides.

## [0.1.0] - Initial MVP

### Added

- Python 3.11 project foundation with setuptools packaging.
- `src/` package layout with typed modules.
- Argparse CLI with `--domain`, `--config`, and `--verbose`.
- YAML configuration loading with `pathlib` and typed helper functions.
- Centralized console and file logging.
- Shared dataclasses for targets, tool results, and reports.
- Lightweight normalization helpers for stable strings, URLs, hostnames, and
  output filenames.
- Safe subprocess execution helper with timeout, environment, working-directory,
  stdout, and stderr support.
- External binary detection with clear missing-tool errors.
- Lightweight wrappers for `subfinder`, `httpx`, and `gau`.
- Configurable tool settings for enabled state, binary path, and timeout.
- Main recon workflow for subdomain discovery, live host detection, historical
  URL collection, and processed output files.
- Plain markdown reporting with output locations and run summaries.
- SQLite run history in `data/reconbot.db` using the standard library.
- Basic recon diff support for added and removed subdomains and live URLs.
- Developer tooling with Ruff, mypy, pytest, pre-commit, a venv-aware Makefile,
  and GitHub Actions CI.
- Project documentation covering setup, architecture, security, tool
  installation, roadmap, and changelog.

### Security

- Documented authorized-use-only scope.
- Kept exploitation and vulnerability scanning out of scope.
- Enforced the no `shell=True` rule for external command execution.
- Added repository hygiene rules for virtualenvs, caches, logs, generated recon
  data, reports, and secrets.

### Notes

- This release establishes the first usable Reconbot MVP for authorized
  reconnaissance automation.
- Dashboards, notifications, plugin frameworks, heavy ORM/database systems, and
  deployment infrastructure remain intentionally deferred.
