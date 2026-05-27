# Security

Reconbot is authorized-use-only software for security research and bug bounty
reconnaissance. Only run it against assets you own or assets where you have
explicit written permission and a defined scope.

## Authorized Scope

The project must not include exploit modules, credential harvesting, persistence,
evasion, malware behavior, or functionality designed to bypass authorization.
Prefer passive recon by default. Any future active behavior must be explicit,
configurable, documented, and safe for approved testing contexts.

## No `shell=True`

Reconbot must never use `shell=True`. Commands must be passed as argument lists
to `subprocess.run` through the shared subprocess runner. This avoids shell
expansion, command injection risks, and inconsistent quoting behavior.

## Secrets Handling

Secrets belong in local environment variables, a local `.env` file, or a secret
manager outside the repository. `.env.example` may document variable names, but
must not contain real credentials.

Do not log secrets. Do not include secrets in generated reports, test fixtures,
or example output.

## Generated Data Handling

Generated recon data belongs under ignored runtime directories such as `data/`,
`reports/`, and `logs/`. Keep only `.gitkeep` placeholders in those directories.
Review generated files before sharing them because recon output can contain
target details, tokens, internal hostnames, or other sensitive information.

## Never Commit

Do not commit:

- virtual environments such as `.venv/`;
- Python caches such as `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, or
  `.ruff_cache/`;
- generated recon data under `data/`;
- generated reports under `reports/`;
- log files under `logs/`;
- `.env` files or other local secret files;
- private keys, certificates, API tokens, session cookies, or credentials;
- tool outputs from real targets unless they are sanitized and explicitly meant
  to be documentation fixtures.
