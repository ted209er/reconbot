# AGENTS.md

## Project Purpose

This repository is for authorized security reconnaissance only.

## Security Rules

- Do not add exploit modules.
- Do not add credential harvesting.
- Prefer passive recon.
- Never use shell=True.
- Keep external tool execution isolated in src/reconbot/tools/.

 ## Engineering Standards

 - Use type hints.
 - Use pathlib.
 - Add tests for every module.
 - Prefer standard library solutions when practical.
 - Keep code simple and readable.
 - Keep modules focused and reasonably small.
 - Preserve backward compatibility where practical.

 ## Workflow Standards

 - Default branch is develop.
 - Create feature branches for new work.
 - Update README.md when user-facing behavior changes.
 - Update CHANGELOG.md when features are added.
 - Update relevant docs under docs/.
 - Run make validate before completing work.
 - Run git diff --check before completing work.

 ## Feature Documentation

 For completed features:

 - Append a summary to docs/feature-history.md

 Include:

 - Purpose
 - Files Added
 - Files Modified
 - New Commands
 - Design Decisions
 - Follow-Up Opportunities
 - Verification Results
 - Package default configuration files with the application.
 - Prefer workspace-aware paths over repository-relative paths.












