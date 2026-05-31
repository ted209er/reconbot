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
