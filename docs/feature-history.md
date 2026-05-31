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
