# Feature History

## Scan Profiles

### Purpose

Allow users to choose lightweight, standard, or deep passive reconnaissance
behavior without adding active testing capabilities.

### Files Added

- `src/reconbot/profiles.py`
- `tests/test_profiles.py`
- `docs/feature-history.md`

### Files Modified

- `src/reconbot/cli.py`
- `src/reconbot/main.py`
- `src/reconbot/history.py`
- `src/reconbot/reporting.py`
- `src/reconbot/exporting.py`
- `tests/test_cli.py`
- `tests/test_history.py`
- `tests/test_reporting.py`
- `tests/test_exporting.py`
- `tests/test_main.py`
- `README.md`
- `docs/architecture.md`
- `CHANGELOG.md`

### New Commands

```bash
reconbot --domain example.com --profile light
reconbot --domain example.com --profile standard
reconbot --domain example.com --profile deep
```

### Design Decisions

- Profiles adjust existing passive tool enablement and timeout values only.
- `standard` preserves existing configured behavior and remains the default.
- `light` keeps core passive sources, disables screenshots, and caps timeouts.
- `deep` enables all currently supported passive sources and screenshots, with
  longer timeout floors.
- The selected profile is stored in startup output, reports, JSON exports, and
  SQLite run history.

### Follow-Up Opportunities

- Add profile-aware scheduling examples if scheduled profile usage becomes
  common.
- Revisit timeout bounds when additional passive sources are introduced.

### Verification Results

- `make validate`
- `git diff --check`

## Investigation Guidance

### Purpose

Use existing passive findings to suggest safe, explainable manual investigation
checks for authorized security research.

### Files Added

- `src/reconbot/guidance.py`
- `tests/test_guidance.py`

### Files Modified

- `src/reconbot/main.py`
- `src/reconbot/reporting.py`
- `src/reconbot/exporting.py`
- `tests/test_reporting.py`
- `tests/test_exporting.py`
- `README.md`
- `docs/architecture.md`
- `CHANGELOG.md`
- `docs/feature-history.md`

### New Commands

- None.

### Design Decisions

- Generate suggestions from existing findings only: asset categories,
  technologies, URL keywords, high-interest score, new asset status, and
  screenshot availability.
- Keep the guidance engine rule-based, deterministic, typed, and explainable.
- Include a title, rationale, safe manual approach, evidence guidance, and
  explicit safety note for every check.
- Scope all guidance to authorized targets, owned test accounts, and
  non-destructive validation.
- Exclude exploit payloads, automated scanning, brute forcing, credential
  testing, destructive checks, and requests against third-party user data.

### Follow-Up Opportunities

- Add optional category-based guidance filtering if reports become too verbose.
- Add report-level guidance severity only after a separate scoring review.

### Verification Results

- `make validate`
- `git diff --check`

## Technology Categorization V2

### Purpose

Make passive reconnaissance reports more actionable by classifying discovered
assets into security-relevant categories with human-readable confidence.

### Files Added

- `src/reconbot/tools/gowitness.py`
- `tests/test_gowitness.py`

### Files Modified

- `src/reconbot/technology_categories.py`
- `src/reconbot/fingerprinting.py`
- `src/reconbot/tools/httpx.py`
- `src/reconbot/screenshots.py`
- `src/reconbot/main.py`
- `src/reconbot/reporting.py`
- `src/reconbot/exporting.py`
- `tests/test_technology_categories.py`
- `tests/test_fingerprinting.py`
- `tests/test_httpx.py`
- `tests/test_screenshots.py`
- `tests/test_reporting.py`
- `tests/test_exporting.py`
- `README.md`
- `docs/architecture.md`
- `CHANGELOG.md`
- `docs/feature-history.md`

### New Commands

- None.

### Design Decisions

- Preserve the existing technology categorization and prioritization APIs.
- Add asset categories for Authentication, API, Administrative, Commerce, CDN,
  Marketing, Documentation, Developer Tools, Source Control, Monitoring, Cloud
  Infrastructure, and SaaS Platforms.
- Classify only passive metadata: observed technology fingerprints, URLs, and
  optional response headers, page titles, and known platform indicators.
- Record deterministic `low`, `medium`, or `high` confidence from signal
  quality and diversity.
- Include category summaries and category-sorted asset lists in markdown, plus
  structured categories, confidence, and indicators in JSON exports.

### Follow-Up Opportunities

- Preserve more passive metadata from future wrapper output when supported by
  installed tool versions.
- Add category-aware prioritization only after scoring changes are explicitly
  reviewed.

### Verification Results

- `make validate`
- `git diff --check`

## Collection Status

### Purpose

Make passive collection quality visible as first-class evidence so users can
distinguish complete runs from partial or failed runs without reading log files.

### Files Added

- `src/reconbot/collection_status.py`
- `tests/test_collection_status.py`

### Files Modified

- `src/reconbot/main.py`
- `src/reconbot/history.py`
- `src/reconbot/reporting.py`
- `src/reconbot/exporting.py`
- `src/reconbot/screenshots.py`
- `src/reconbot/tools/subfinder.py`
- `src/reconbot/tools/assetfinder.py`
- `src/reconbot/tools/crtsh.py`
- `src/reconbot/tools/httpx.py`
- `src/reconbot/tools/gau.py`
- `src/reconbot/tools/waybackurls.py`
- `tests/test_main.py`
- `tests/test_history.py`
- `tests/test_reporting.py`
- `tests/test_exporting.py`
- `tests/test_subfinder.py`
- `tests/test_assetfinder.py`
- `tests/test_crtsh.py`
- `tests/test_httpx.py`
- `tests/test_gau.py`
- `tests/test_waybackurls.py`
- `tests/test_screenshots.py`
- `tests/test_workspaces.py`
- `README.md`
- `docs/architecture.md`
- `CHANGELOG.md`
- `docs/feature-history.md`

### New Commands

- None.

### Design Decisions

- Keep existing passive wrapper return values unchanged and append optional
  typed collection evidence for backward compatibility.
- Record `SUCCESS`, `ZERO_RESULTS`, `FAILED`, `TIMED_OUT`, and `DISABLED`
  states with source, target, count, optional return code, and concise error.
- Record zero-input `httpx` and `gowitness` stages explicitly.
- Derive deterministic `COMPLETE`, `PARTIAL`, and `FAILED` run completeness.
- Persist collection evidence in SQLite and include it in markdown and JSON.

### Follow-Up Opportunities

- Add local-only doctor capability checks for screenshot browser dependencies.
- Add screenshot artifact verification and per-URL failure diagnostics.
- Compare run diffs against the most recent complete run when partial runs are
  present.

### Verification Results

- `make validate`
- `git diff --check`

## Screenshot Diagnostics

### Purpose

Make screenshot failures visible, actionable, and auditable while keeping
capture passive and local environment checks target-free.

### Files Added

- None.

### Files Modified

- `src/reconbot/tools/gowitness.py`
- `src/reconbot/screenshots.py`
- `src/reconbot/doctor.py`
- `src/reconbot/main.py`
- `src/reconbot/history.py`
- `src/reconbot/reporting.py`
- `src/reconbot/exporting.py`
- `tests/test_gowitness.py`
- `tests/test_screenshots.py`
- `tests/test_doctor.py`
- `tests/test_history.py`
- `tests/test_reporting.py`
- `tests/test_exporting.py`
- `tests/test_main.py`
- `tests/test_workspaces.py`
- `README.md`
- `docs/tool-installation.md`
- `docs/architecture.md`
- `CHANGELOG.md`
- `docs/feature-history.md`

### New Commands

- None.

### Design Decisions

- Record typed per-URL `SUCCESS`, `FAILED`, `TIMED_OUT`, and `NO_ARTIFACT`
  screenshot diagnostics with return code and concise error.
- Accept screenshot success only when the expected artifact exists and has a
  size greater than zero.
- Map screenshot diagnostics into the shared collection-status model so
  failures affect deterministic run completeness.
- Persist diagnostics in SQLite and expose `screenshot_status` and
  `screenshot_error` JSON fields plus markdown warnings.
- Keep doctor extensions local-only: executable visibility, `gowitness version`
  execution, and Chrome or Chromium availability.
- Keep all external process construction and execution in
  `src/reconbot/tools/gowitness.py`.

### Follow-Up Opportunities

- Support configurable browser paths when browser installations are not
  visible on `PATH`.
- Confirm artifact naming across supported `gowitness` versions and add a
  compatibility adapter if needed.

### Verification Results

- `make validate`
- `git diff --check`

## Historical URL Intelligence

### Purpose

Transform large passive historical URL collections into structured,
explainable leads for authorized manual investigation.

### Files Added

- `src/reconbot/url_intelligence.py`
- `tests/test_url_intelligence.py`

### Files Modified

- `src/reconbot/main.py`
- `src/reconbot/history.py`
- `src/reconbot/reporting.py`
- `src/reconbot/exporting.py`
- `tests/test_main.py`
- `tests/test_history.py`
- `tests/test_exporting.py`
- `tests/test_workspaces.py`
- `README.md`
- `docs/architecture.md`
- `CHANGELOG.md`
- `docs/feature-history.md`

### New Commands

- None.

### Design Decisions

- Preserve the existing flat `historical_urls.txt` export for backward
  compatibility.
- Classify only URLs already collected by passive sources. Do not crawl, fetch
  archived pages, probe targets, or test vulnerabilities.
- Use `urllib.parse`, suffix analysis, and explicit keyword mappings for
  deterministic, explainable multi-category assignments.
- Preserve `gau` and `waybackurls` provenance for each merged URL.
- Export the full structured set to TSV, JSON, and SQLite while limiting
  markdown output to the top 25 historical leads.
- Clearly label historical URLs as `Historical Lead`, not
  `Current Observation`, and mark reachability as `unverified`.

### Follow-Up Opportunities

- Add configuration overrides for keyword mappings if engagement-specific
  terminology becomes common.
- Add historical URL category filtering to future offline review tools.

### Verification Results

- `make validate`
- `git diff --check`

## Review Dossier

### Purpose

Generate a local-only investigation dossier that combines existing workspace
evidence into a prioritized, explainable manual review plan.

### Files Added

- `src/reconbot/planning.py`
- `tests/test_planning.py`

### Files Modified

- `src/reconbot/cli.py`
- `src/reconbot/main.py`
- `src/reconbot/exporting.py`
- `tests/test_cli.py`
- `tests/test_exporting.py`
- `README.md`
- `docs/architecture.md`
- `CHANGELOG.md`
- `docs/feature-history.md`

### New Commands

```bash
reconbot plan --workspace PATH
```

### Design Decisions

- Read existing workspace JSON exports, matching SQLite run history in
  read-only mode, and `scope.txt`.
- Write `reports/investigation-plan.md` and
  `reports/investigation-plan.json` under the workspace.
- Combine collection quality, changes, asset and technology categories,
  historical URL intelligence, prioritization scores, and safe manual
  investigation guidance.
- Clearly distinguish `Current Observation` from `Historical Lead`, and
  `In Scope` from `Unknown Scope`.
- Retain `unverified` reachability for archived URL leads and flag unknown-scope
  assets for owner confirmation.
- Keep planning local-only: no recon, target contact, external tools,
  AI-generated findings, vulnerability claims, or automated testing.

### Follow-Up Opportunities

- Add an optional run selector when users need dossiers for older workspace
  exports.
- Add offline filters for large dossiers if users need narrower review queues.

### Verification Results

- `make validate`
- `git diff --check`
