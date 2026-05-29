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

## History Layer

`src/reconbot/history.py` stores completed run summaries in SQLite using only the
standard library `sqlite3` module. The database lives at `data/reconbot.db`.

The history layer is intentionally small. It creates the `runs` table when
needed, records completed runs, and lists recent runs. It does not implement
migrations, diffing, dashboards, or analytics.

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
