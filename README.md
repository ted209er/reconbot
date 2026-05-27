# Reconbot

Reconbot is a modular Python reconnaissance automation toolkit foundation for
authorized security research and bug bounty recon. The current codebase is an
application foundation only: it parses CLI arguments, loads YAML configuration,
configures logging, models workflow state, and provides a safe subprocess
execution helper. It does not include active recon integrations yet.

## Authorized Use Only

Use Reconbot only against assets you own or have explicit written authorization
to test. Do not use this project for exploitation, credential harvesting,
evasion, persistence, or activity outside an approved scope. Future recon
modules must preserve this boundary.

## Current Architecture

- `src/reconbot/cli.py` builds the argparse CLI and supports `--domain`,
  `--config`, and `--verbose`.
- `src/reconbot/config.py` loads YAML configuration with `pathlib` and typed
  helper functions.
- `src/reconbot/logging_config.py` centralizes console and file logging.
- `src/reconbot/models.py` defines `ReconTarget`, `ToolResult`, and
  `ReconReport`.
- `src/reconbot/main.py` contains the placeholder orchestration flow.
- `src/reconbot/utils/subprocess_runner.py` wraps `subprocess.run` safely,
  captures output, supports timeouts, and returns `ToolResult` objects.
- `src/reconbot/tools/` contains lightweight tool wrappers such as the subfinder,
  httpx, and gau wrappers. Wrappers build safe argument lists, call shared
  helpers, and keep parsing local to the tool.
- `src/reconbot/modules/` is reserved for orchestration modules that compose tool
  wrappers into workflow phases.
- `configs/default.yaml` contains the default application configuration.
- `docs/` contains architecture and security notes.

## Setup

Install Python 3.11 or newer, then create a local virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If your system exposes Python 3.11 as `python3`, this also works:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Running

```bash
reconbot --domain example.com --config configs/default.yaml --verbose
```

The workflow runs subdomain discovery, live host detection, and historical URL
collection for the authorized domain. Processed outputs are written to
`data/processed/`.

Tool wrappers expect their external binaries to be installed separately and
available on `PATH`. The current wrappers expect ProjectDiscovery `subfinder`
and `httpx`, plus `gau`.

## Validation

Run these before opening a PR:

```bash
pytest
ruff check .
mypy src tests
git diff --check
```

## Pre-Commit

Install the Git hooks after setting up the virtual environment:

```bash
pre-commit install
```

Run the hooks manually:

```bash
pre-commit run --all-files
```

## MVP Roadmap

1. Keep the application foundation stable: CLI, config loading, logging, models,
   subprocess execution, and tests.
2. Define a consistent tool wrapper interface that returns `ToolResult`.
3. Add passive, authorized-only recon wrappers behind configuration flags.
4. Add report serialization for generated findings without committing generated
   outputs.
5. Expand module orchestration while keeping each tool isolated and testable.
