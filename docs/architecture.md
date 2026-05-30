# Architecture

Reconbot uses a small `src` layout so application code is importable as the
`reconbot` package while tests remain outside the package.

## Source Layout

- `src/reconbot/cli.py` owns command-line parsing and should stay free of
  workflow logic.
- `src/reconbot/config.py` owns YAML loading and typed access helpers.
- `src/reconbot/config_loader.py` owns packaged default configuration discovery
  and loading.
- `src/reconbot/logging_config.py` owns logging setup for console and file
  output.
- `src/reconbot/models.py` owns shared dataclasses used across orchestration,
  wrappers, and reporting.
- `src/reconbot/main.py` owns top-level orchestration for the CLI entry point.
- `src/reconbot/exporting.py` owns structured JSON export generation.
- `src/reconbot/workspaces.py` owns optional engagement workspace resolution,
  layout creation, and workspace artifact paths.
- `src/reconbot/fingerprinting.py` owns passive technology fingerprinting.
- `src/reconbot/technology_categories.py` groups fingerprinted technologies into
  simple report and scoring categories.
- `src/reconbot/prioritization.py` owns rule-based asset prioritization.
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

Config loader code should use package resources to find the installed default
config. It should not generate environment-specific configs, download remote
configs, or prompt users through setup wizards.

Logging setup should be centralized so modules only need `logging.getLogger`.

Models should stay simple and serializable. Shared state should move through
dataclasses such as `ReconTarget`, `ToolResult`, and `ReconReport`.

## Workspace Layer

`src/reconbot/workspaces.py` keeps application code separate from engagement
data when `--workspace PATH` is provided. It resolves the workspace path,
creates the standard lightweight layout, and returns typed paths for
orchestration:

```text
workspace/
├── data/
├── reports/
├── screenshots/
├── findings/
├── notes/
└── scope.txt
```

Workspace mode is optional. Without `--workspace`, Reconbot keeps the existing
config-driven output paths. With `--workspace`, generated processed data,
reports, JSON exports, screenshots, and SQLite run history use workspace paths.

The workspace layer does not implement multi-user coordination, cloud storage,
synchronization, dashboards, or background services.

## Default Config

Reconbot includes `src/reconbot/configs/default.yaml` as package data so normal
and editable installs can run without a repo-local config path:

```bash
reconbot --domain example.com
```

`src/reconbot/config_loader.py` exposes `get_default_config_path()` and
`load_default_config()` using standard-library package resource APIs. When
`--config` is omitted, orchestration loads the packaged default config. When
`--config PATH` is supplied, orchestration uses that custom file and preserves
the previous override behavior.

## Export Layer

`src/reconbot/exporting.py` builds deterministic JSON exports for automation and
future integrations. Exports are written to
`reports/json/<safe-target-name>.json` after markdown report generation when
`output.write_json` is enabled. Workspace runs write JSON exports under
`<workspace>/reports/json/`.

The export layer uses only the standard library. It serializes run metadata,
workspace path, output paths, counts, discoveries, passive source counts,
technology summaries and changes, technology categories and category totals,
screenshot paths and changes, prioritized assets, and the markdown report path.
It does not add APIs, web services, dashboards, or external serialization
libraries.

## Prioritization Layer

`src/reconbot/prioritization.py` assigns simple explainable scores to live URLs.
It is deterministic and rule-based. Signals include new subdomains, new live
URLs, newly observed technologies, admin/login/auth keywords, API keywords, and
screenshot availability.

Prioritization does not use machine learning, AI scoring, external services,
risk databases, vulnerability detection, or exploit logic. It only helps users
review interesting discovered assets first.

## Fingerprinting Layer

`src/reconbot/fingerprinting.py` enriches live URLs with passive technology
signals. It reuses the configured `httpx` binary with JSON technology detection
options and parses only the returned metadata.

The fingerprinting layer records indicators such as web servers, CDNs, reverse
proxies, frameworks, CMSs, and language hints. It does not perform vulnerability
scanning, exploit checks, brute force, credential enumeration, browser
automation, or active security testing.

## Technology Categorization

`src/reconbot/technology_categories.py` groups fingerprinted technologies into
small deterministic categories for reports, JSON exports, and prioritization.
The current categories are Infrastructure, Framework, CMS, Identity, Language,
and Unknown. Categorization is rule-based and intentionally simple so the
mapping stays easy to read and extend.

Priority scoring uses the category layer as one more explainable signal: Identity
technologies add a small bonus, while the rest of the scoring rules remain
unchanged and deterministic.

## Screenshot Layer

`src/reconbot/screenshots.py` captures screenshots for discovered live URLs
using the configured external `gowitness` binary. Screenshots run after
technology fingerprinting and before historical URL collection.

Screenshot paths are deterministic and stored under
`reports/screenshots/<safe-target-name>/`, or under
`<workspace>/screenshots/<safe-target-name>/` when a workspace is configured.
The layer records screenshot metadata in SQLite, including URL, path, and
capture timestamp. Reports compare the current screenshot URL set with the
latest previous run for the same target. This is target-level history only:
Reconbot does not compare pixels, hash image contents, run OCR, add visual
regression testing, or add Playwright, Selenium, browser automation frameworks,
notifications, or dashboards.

## History Layer

`src/reconbot/history.py` stores completed run summaries and selected per-run
findings in SQLite using only the standard library `sqlite3` module. The
database lives at `data/reconbot.db`.
Workspace runs store the database at `<workspace>/data/reconbot.db`, which keeps
engagement run history with the rest of the engagement artifacts.

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

The subfinder, assetfinder, crt.sh, httpx, gau, waybackurls, and screenshot
wrappers follow this pattern: they accept typed inputs, call `run_command()` with
argument lists, and parse output into sorted unique results.

Subdomain discovery merges passive output from subfinder, assetfinder, and
crt.sh. Historical URL discovery merges passive output from gau and waybackurls.
Reports and JSON exports include a discovery source summary so users can see how
many results came from each source.

Tool runtime settings are loaded from the small `tools:` section in YAML config.
Each wrapper can receive an enabled flag, binary name/path, and timeout from the
main workflow. Disabled tools are skipped by orchestration, and detection only
checks enabled binaries.

Higher-level modules under `src/reconbot/modules/` should compose wrappers into
workflow steps. They should not duplicate subprocess execution behavior.
