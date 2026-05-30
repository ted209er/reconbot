# Reconbot Roadmap

Reconbot is for authorized security research and bug bounty recon only. The
roadmap keeps that boundary explicit: build useful reconnaissance workflow
support without exploitation, vulnerability scanning, or unsafe automation.

## v0.1 Foundation

Completed:

- Python 3.11 project foundation with setuptools, pytest, Ruff, and mypy.
- Argparse CLI with domain, config, and verbose options.
- YAML configuration loading.
- Centralized console and file logging.
- Safe subprocess runner with no `shell=True`.
- Lightweight wrappers for `subfinder`, `httpx`, and `gau`.
- Simple orchestration flow for subdomains, live URLs, and historical URLs.
- Plain markdown reports.
- SQLite run history in `data/reconbot.db`.
- Basic recon diff reporting for subdomains and live URLs.
- GitHub Actions CI, pre-commit config, and venv-aware Makefile.

## v0.2 Usability

Upcoming priorities:

- Add a changelog and keep release notes short.
- Improve report readability for run diffs.
- Add export formats such as JSON and CSV.
- Add screenshot support for live web targets.
- Improve CLI help and examples as workflows grow.

## v0.3 Continuous Recon

Upcoming priorities:

- Support scheduled runs without adding deployment infrastructure.
- Make repeat runs easier to manage locally.
- Improve comparison output between historical runs.
- Keep generated data out of git by default.

## v0.4 Enrichment

Upcoming priorities:

- Add technology fingerprinting.
- Add lightweight metadata enrichment for discovered assets.
- Keep enrichment optional and configuration-driven.
- Prefer simple wrappers over complex plugin systems.

## Future Ideas

- Better report templates while staying plain and portable.
- Configurable output retention.
- More passive recon wrappers for authorized scopes.
- Safer review workflows before sharing generated recon data.

## Not Now

Intentionally deferred:

- Exploitation.
- Vulnerability scanning.
- Dashboards.
- Notifications.
- Plugin frameworks.
- Heavy database or ORM systems.
