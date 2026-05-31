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
  `--config`, `--workspace`, `--profile`, and `--verbose`.
- `src/reconbot/config.py` loads YAML configuration with `pathlib` and typed
  helper functions.
- `src/reconbot/config_loader.py` loads the packaged default configuration when
  users do not pass `--config`.
- `src/reconbot/logging_config.py` centralizes console and file logging.
- `src/reconbot/models.py` defines `ReconTarget`, `ToolResult`, and
  `ReconReport`.
- `src/reconbot/main.py` contains the placeholder orchestration flow.
- `src/reconbot/profiles.py` applies lightweight passive scan profiles to
  existing tool settings.
- `src/reconbot/workspaces.py` resolves and creates optional engagement
  workspaces for generated recon data.
- `src/reconbot/utils/subprocess_runner.py` wraps `subprocess.run` safely,
  captures output, supports timeouts, and returns `ToolResult` objects.
- `src/reconbot/tools/` contains lightweight tool wrappers such as the
  subfinder, assetfinder, crt.sh, httpx, gau, and waybackurls wrappers.
  Wrappers build safe argument lists, call shared helpers, and keep parsing
  local to the tool.
- `src/reconbot/modules/` is reserved for orchestration modules that compose tool
  wrappers into workflow phases.
- `configs/default.yaml` mirrors the packaged default application
  configuration.
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

## Quick Start

Set up Python, install Reconbot, validate the repo, and run a small authorized
recon workflow:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

make validate

reconbot --domain example.com
```

Reconbot uses external binaries for tool wrappers. Install `subfinder`,
`assetfinder`, `httpx`, `gau`, `waybackurls`, and `gowitness` before running
enabled tools. Certificate Transparency lookup uses the public crt.sh service
through `curl`. See
[Tool Installation](docs/tool-installation.md) for Ubuntu, WSL Ubuntu, and macOS
commands.

## Feature-To-Tool Map

| Feature | Tool |
| --- | --- |
| Subdomain Discovery | `subfinder` |
| Subdomain Discovery | `assetfinder` |
| Certificate Transparency | `crt.sh` through `curl` |
| Historical URLs | `gau` |
| Historical URLs | `waybackurls` |
| Fingerprinting | `httpx` |
| Screenshots | `gowitness` |

## Verify Your Environment

After installing external tools, confirm Reconbot can find the expected
binaries:

```bash
subfinder -version
assetfinder --help
httpx -version
gau --help
waybackurls --help
gowitness version
```

`crt.sh` is a web source, not a local binary. Reconbot calls it with `curl`,
which is installed by default on many systems and included in the full setup
steps in [docs/tool-installation.md](docs/tool-installation.md).

## First Run

From the repo root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

make validate

reconbot --help
reconbot doctor
reconbot --domain example.com
```

Use only domains you own or have explicit written authorization to test. If
`reconbot --help` works but a real run fails immediately, check the missing
binary message and run the matching command in "Verify Your Environment".

## Doctor

Run the environment health check before your first recon run:

```bash
reconbot doctor
reconbot doctor --workspace ~/Recon/hackerone/example
```

The doctor command checks Python 3.11+, packaged default config loading, SQLite,
optional workspace structure, and external tool availability. It does not
contact targets and does not run recon. Results end with `HEALTHY`, `WARNINGS`,
or `ERROR`.

## Running From A Workspace

Keep generated recon output outside the Git checkout when you are working
multiple authorized targets. A simple layout is:

```text
~/Recon/company-a
~/Recon/company-b
```

Use `--workspace` to keep engagement data outside the Git checkout:

```bash
reconbot \
  --domain example.com \
  --workspace ~/Recon/hackerone/example
```

Reconbot creates the workspace if needed:

```text
workspace/
├── data/
├── reports/
├── screenshots/
├── findings/
├── notes/
└── scope.txt
```

When `--workspace` is provided, generated reports, screenshots, JSON exports,
processed data, and SQLite run history are written under that workspace. Without
`--workspace`, Reconbot preserves the existing config-driven output behavior.
When `--config` is omitted, Reconbot uses its packaged default config.

## Running

```bash
reconbot --domain example.com --config configs/default.yaml --verbose
reconbot --domain example.com --config configs/default.yaml --run-name daily
reconbot --domain example.com --workspace ~/Recon/hackerone/example
reconbot doctor --workspace ~/Recon/hackerone/example
```

Startup output shows the target, config path, enabled tools and configured
binaries, progress between stages, summary counts, and the generated report and
output file locations.
It also prints `Using packaged default config` when `--config` is omitted, or
`Using config:` with the custom path when `--config` is supplied.

## Scan Profiles

Choose a passive reconnaissance profile with `--profile`. The default is
`standard`:

```bash
reconbot --domain example.com --profile light
reconbot --domain example.com --profile standard
reconbot --domain example.com --profile deep
```

| Profile | Behavior |
| --- | --- |
| `light` | Uses core passive sources, disables screenshots, and caps tool timeouts at 60 seconds. |
| `standard` | Preserves the configured default workflow. |
| `deep` | Enables all currently supported passive sources and screenshots, with longer timeout floors. |

Profiles adjust existing passive behavior only. They do not add vulnerability
scanning, exploitation, brute forcing, credential attacks, directory
enumeration, or port scanning. The selected profile is shown at startup and
stored in reports, JSON exports, and run history.

The workflow runs passive subdomain discovery, live host detection, passive
technology fingerprinting, screenshot capture, and historical URL collection for the authorized domain.
Processed outputs are written to `data/processed/`, and a plain markdown report
is written to `reports/` unless `--workspace` is provided.
Completed run summaries are also stored in a local SQLite database at
`data/reconbot.db`, or `<workspace>/data/reconbot.db` for workspace runs, so
future features can compare runs without parsing report files.
Reports include a small comparison against the most recent previous run for the
same target, including added and removed subdomains and live URLs.
Reports also include a technology summary and technology changes detected across
live URLs.
Those technologies are grouped into simple categories in the report and JSON
export, including Infrastructure, Framework, CMS, Identity, Language, and
Unknown.
Screenshots for live URLs are stored under
`reports/screenshots/<safe-target-name>/`, or
`<workspace>/screenshots/<safe-target-name>/` for workspace runs, and linked
from markdown reports.
Reconbot records screenshot metadata in SQLite and reports new or removed
screenshot targets by URL. It does not compare pixels, hash image contents, run
OCR, or perform visual regression testing.
Structured JSON exports are written to `reports/json/<safe-target-name>.json`,
or `<workspace>/reports/json/<safe-target-name>.json` for workspace runs, for
automation, scripting, and future integrations.
Reconbot also builds a rule-based high-interest asset list to help review the
most relevant live URLs first. Scores are explainable and deterministic:
new subdomains and new live URLs add 5 points each, new technologies add 4,
Identity technologies add 3,
admin/login/auth URL keywords add 3, API keywords add 2, and screenshots add 1.

Tool wrappers expect their external binaries to be installed separately and
available on `PATH`. The current wrappers expect ProjectDiscovery `subfinder`
and `httpx`, `assetfinder`, `gau`, `waybackurls`, `curl` for crt.sh lookups, and
`gowitness` for screenshots.

Subdomain discovery merges passive results from `subfinder`, `assetfinder`, and
crt.sh. Historical URL discovery merges passive results from `gau` and
`waybackurls`. Reports and JSON exports include per-source discovery counts.

Technology fingerprinting reuses the configured `httpx` binary with passive
technology detection options:

```bash
httpx -silent -json -tech-detect -u https://example.com
```

Reconbot parses the JSON output for technology names such as web servers, CDNs,
CMSs, frameworks, and language indicators.

Screenshot capture uses the configured `gowitness` binary:

```bash
gowitness scan single --url https://example.com --screenshot-path reports/screenshots/example-com
```

## Scheduling

Reconbot stays scheduler-agnostic. Use cron, systemd timers, or Windows Task
Scheduler for WSL to run the normal CLI command:

```bash
cd /home/user/Repos/reconbot
.venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name daily
```

See [docs/scheduling.md](docs/scheduling.md) for cron, systemd timer, and WSL
examples.

Tool settings live in the packaged default config. The repo copy at
`configs/default.yaml` is useful as a reference or a starting point for a custom
config. Each tool supports a small set of settings:

```yaml
output:
  processed_dir: data/processed
  reports_dir: reports
  json_exports_dir: reports/json
  write_json: true
tools:
  subfinder:
    enabled: true
    binary: subfinder
    timeout: 120
  assetfinder:
    enabled: true
    binary: assetfinder
    timeout: 120
  crtsh:
    enabled: true
    binary: curl
    timeout: 120
  waybackurls:
    enabled: true
    binary: waybackurls
    timeout: 120
  screenshots:
    enabled: true
    binary: gowitness
    timeout: 300
```

Use `enabled: false` to skip a tool, `binary` to point at a custom executable
path or name, and `timeout` to set the per-tool subprocess timeout in seconds.
Use `output.write_json: false` to skip JSON export generation.

Reconbot checks for required external binaries before running the workflow. If a
tool is missing, install it from its upstream project and confirm the binary is
available on `PATH` before rerunning:

```bash
subfinder -version
assetfinder --help
httpx -version
gau --help
waybackurls --help
curl --version
gowitness version
```

## Validation

Run these before opening a PR:

```bash
pytest
ruff check .
mypy src tests
git diff --check
```

The same commands are available through `make`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

make validate
make test
make lint
```

Makefile targets use tools from the local virtual environment directly, such as
`.venv/bin/ruff`, so you do not need to modify `PATH` before running them.

Additional targets:

```bash
make lint
make typecheck
make test
make validate
make format
```

## CI

Pushes and pull requests automatically run the same lightweight validation in
GitHub Actions: Ruff, mypy, and pytest on Python 3.11.

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

See [docs/roadmap.md](docs/roadmap.md) for the current lightweight project
roadmap.

1. Keep the application foundation stable: CLI, config loading, logging, models,
   subprocess execution, and tests.
2. Define a consistent tool wrapper interface that returns `ToolResult`.
3. Add passive, authorized-only recon wrappers behind configuration flags.
4. Add report serialization for generated findings without committing generated
   outputs.
5. Expand module orchestration while keeping each tool isolated and testable.
