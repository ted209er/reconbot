# Architecture

Reconbot uses a small `src` layout so application code is importable as the
`reconbot` package while tests remain outside the package.

## Source Layout

- `src/reconbot/cli.py` owns command-line parsing and should stay free of
  workflow logic.
- `src/reconbot/config.py` owns YAML loading and typed access helpers.
- `src/reconbot/logging_config.py` owns logging setup for console and file
  output.
- `src/reconbot/models.py` owns shared dataclasses used across orchestration,
  wrappers, and reporting.
- `src/reconbot/main.py` owns top-level orchestration for the CLI entry point.
- `src/reconbot/fingerprinting.py` owns passive technology fingerprinting.
- `src/reconbot/screenshots.py` owns passive screenshot capture.
- `src/reconbot/history.py` owns the lightweight SQLite run history.
- `src/reconbot/utils/` contains shared helpers that are not recon tools.
- `src/reconbot/tools/` is reserved for future wrappers around external tools or
  APIs.
- `src/reconbot/modules/` is reserved for higher-level workflow modules that
  compose tools into recon phases.

## Module Boundaries

CLI code should parse input and hand typed values to orchestration. It should not
call external tools directly.

Configuration code should validate and return typed values. It should not mutate
global state.

Logging setup should be centralized so modules only need `logging.getLogger`.

Models should stay simple and serializable. Shared state should move through
dataclasses such as `ReconTarget`, `ToolResult`, and `ReconReport`.

## Fingerprinting Layer

`src/reconbot/fingerprinting.py` enriches live URLs with passive technology
signals. It reuses the configured `httpx` binary with JSON technology detection
options and parses only the returned metadata.

The fingerprinting layer records indicators such as web servers, CDNs, reverse
proxies, frameworks, CMSs, and language hints. It does not perform vulnerability
scanning, exploit checks, brute force, credential enumeration, browser
automation, or active security testing.

## Screenshot Layer

`src/reconbot/screenshots.py` captures screenshots for discovered live URLs
using the configured external `gowitness` binary. Screenshots run after
technology fingerprinting and before historical URL collection.

Screenshot paths are deterministic and stored under
`reports/screenshots/<safe-target-name>/`. The layer records screenshot metadata
in SQLite and adds captured paths to markdown reports. It does not add
Playwright, Selenium, browser automation frameworks, OCR, image analysis,
notifications, or dashboards.

## History Layer

`src/reconbot/history.py` stores completed run summaries and selected per-run
findings in SQLite using only the standard library `sqlite3` module. The
database lives at `data/reconbot.db`.

The history layer is intentionally small. It creates the `runs`, `subdomains`,
`live_urls`, `technologies`, and `screenshots` tables when needed, records
completed runs, stores selected results, and lists recent runs.

The workflow compares current subdomains, live URLs, and technologies with the
latest previous run for the same target before recording the current run.
Reports show simple added and removed item counts plus the changed values. The
project does not implement migrations, dashboards, analytics, notifications, or
background jobs.

## Subprocess Runner

`src/reconbot/utils/subprocess_runner.py` is the foundation helper for local
process execution. Its responsibilities are:

- call `subprocess.run` with `shell=False`;
- accept commands as argument lists;
- support timeout, environment overrides, and optional working directories;
- capture stdout and stderr;
- log command start, success, nonzero exits, timeouts, and missing executables;
- return `ToolResult` objects instead of raising for normal tool failures.

It should not know about specific recon tools or parse tool-specific output.

## Future Tool Wrapper Pattern

Future wrappers should live under `src/reconbot/tools/` and expose small
functions or classes that accept typed inputs and return `ToolResult` or another
explicit model. A wrapper should build an argument list, call the subprocess
runner when invoking a local binary, and keep parsing logic scoped to that tool.

The subfinder, httpx, and gau wrappers follow this pattern: they accept typed
inputs, call `run_command()` with argument lists, and parse newline-based stdout
into sorted unique results. They expect the external binaries to be installed on
`PATH` and are not wired into orchestration yet.

Tool runtime settings are loaded from the small `tools:` section in YAML config.
Each wrapper can receive an enabled flag, binary name/path, and timeout from the
main workflow. Disabled tools are skipped by orchestration, and detection only
checks enabled binaries.

Higher-level modules under `src/reconbot/modules/` should compose wrappers into
workflow steps. They should not duplicate subprocess execution behavior.
