"""Local-only investigation dossier generation from existing workspace artifacts."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from reconbot.workspaces import resolve_workspace, workspace_paths

CURRENT_OBSERVATION = "Current Observation"
HISTORICAL_LEAD = "Historical Lead"
IN_SCOPE = "In Scope"
UNKNOWN_SCOPE = "Unknown Scope"


class PlanningError(ValueError):
    """Raised when an offline dossier cannot be built from workspace artifacts."""


@dataclass(frozen=True, slots=True)
class ReviewCandidate:
    """One explainable manual review candidate."""

    asset: str
    observation_type: str
    scope_status: str
    priority: int
    evidence: tuple[str, ...]
    reason: tuple[str, ...]
    suggested_checks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvestigationDossier:
    """Structured local-only investigation dossier."""

    workspace: str
    source_export: str
    target: str
    latest_run: Mapping[str, object]
    authorization_reminder: str
    scope_summary: Mapping[str, object]
    collection_quality: tuple[Mapping[str, object], ...]
    new_and_changed_assets: Mapping[str, tuple[str, ...]]
    asset_categories: Mapping[str, object]
    historical_url_intelligence: tuple[Mapping[str, object], ...]
    top_review_candidates: tuple[ReviewCandidate, ...]
    suggested_manual_investigation_plan: tuple[Mapping[str, object], ...]
    owner_confirmation_needed: tuple[str, ...]
    evidence_collection_template: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DossierPaths:
    """Generated dossier artifact paths."""

    markdown: Path
    json: Path


def generate_review_dossier(workspace_path: Path) -> DossierPaths:
    """Build local-only markdown and JSON dossiers from an existing workspace."""
    workspace = resolve_workspace(workspace_path)
    if workspace is None or not workspace.is_dir():
        raise PlanningError(f"workspace directory not found: {workspace_path}")
    paths = workspace_paths(workspace)
    export_path, export = _load_latest_export(paths.json_exports_dir)
    latest_run = _load_latest_run(paths.database_path, target=_string(export.get("target")))
    dossier = build_investigation_dossier(
        workspace=workspace,
        export_path=export_path,
        export=export,
        latest_run=latest_run,
        scope_entries=_read_scope_entries(paths.scope_file),
    )
    markdown_path = paths.reports_dir / "investigation-plan.md"
    json_path = paths.reports_dir / "investigation-plan.json"
    markdown_path.write_text(build_markdown_dossier(dossier), encoding="utf-8")
    json_path.write_text(
        json.dumps(dossier_to_json(dossier), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return DossierPaths(markdown=markdown_path, json=json_path)


def build_investigation_dossier(
    *,
    workspace: Path,
    export_path: Path,
    export: Mapping[str, Any],
    latest_run: Mapping[str, object],
    scope_entries: tuple[str, ...],
) -> InvestigationDossier:
    """Combine existing findings into one deterministic offline review plan."""
    target = _string(export.get("target"))
    scope_rules = tuple(sorted(set(scope_entries) | ({target} if target else set())))
    candidates = _build_candidates(export, scope_rules)
    owner_confirmation = tuple(
        sorted(
            candidate.asset
            for candidate in candidates
            if candidate.scope_status == UNKNOWN_SCOPE
        )
    )
    scope_summary: dict[str, object] = {
        "target": target,
        "scope_file_entries": list(scope_entries),
        "candidate_counts": {
            IN_SCOPE: sum(candidate.scope_status == IN_SCOPE for candidate in candidates),
            UNKNOWN_SCOPE: sum(
                candidate.scope_status == UNKNOWN_SCOPE for candidate in candidates
            ),
        },
    }
    return InvestigationDossier(
        workspace=str(workspace),
        source_export=str(export_path),
        target=target,
        latest_run=latest_run,
        authorization_reminder=(
            "Review only assets covered by written authorization. Confirm ownership and scope "
            "before any manual validation. Historical leads have unverified reachability."
        ),
        scope_summary=scope_summary,
        collection_quality=tuple(_mapping_list(export.get("collection_status"))),
        new_and_changed_assets=_new_and_changed_assets(export),
        asset_categories={
            "assets": _mapping(export.get("asset_categories")),
            "technology_categories": _mapping(export.get("technology_categories")),
            "summary": _mapping(export.get("asset_category_summary")),
        },
        historical_url_intelligence=tuple(
            _mapping_list(export.get("historical_url_intelligence"))
        ),
        top_review_candidates=tuple(candidates),
        suggested_manual_investigation_plan=tuple(
            _mapping_list(export.get("investigation_guidance"))
        ),
        owner_confirmation_needed=owner_confirmation,
        evidence_collection_template=(
            "Asset and observation type",
            "Scope confirmation and authorization reference",
            "Passive evidence and collection source",
            "Manual check performed using non-destructive validation",
            "Observed result with timestamp",
            "Screenshot or response excerpt path",
            "Follow-up decision and owner confirmation",
        ),
    )


def build_markdown_dossier(dossier: InvestigationDossier) -> str:
    """Render a human-readable offline investigation dossier."""
    lines = [
        "# Reconbot Investigation Plan",
        "",
        "## Authorization Reminder",
        "",
        dossier.authorization_reminder,
        "",
        "## Scope Summary",
        "",
        f"- Workspace: `{dossier.workspace}`",
        f"- Source export: `{dossier.source_export}`",
        f"- Target: `{dossier.target}`",
        f"- Latest run status: `{dossier.latest_run.get('run_status', 'unknown')}`",
        "",
    ]
    candidate_counts = _mapping(dossier.scope_summary.get("candidate_counts"))
    lines.extend(
        [
            f"- {IN_SCOPE}: {candidate_counts.get(IN_SCOPE, 0)} candidates",
            f"- {UNKNOWN_SCOPE}: {candidate_counts.get(UNKNOWN_SCOPE, 0)} candidates",
            "",
            "## Collection Quality",
            "",
        ]
    )
    lines.extend(_collection_quality_lines(dossier.collection_quality))
    lines.extend(["", "## New and Changed Assets", ""])
    lines.extend(_changed_asset_lines(dossier.new_and_changed_assets))
    lines.extend(["", "## Asset Categories", ""])
    lines.extend(_asset_category_lines(dossier.asset_categories))
    lines.extend(["", "## Historical URL Intelligence", ""])
    lines.extend(
        [
            "- Classification: Historical Lead",
            "- Reachability: unverified",
            "- Archive presence is not evidence that a URL remains reachable.",
            "",
        ]
    )
    lines.extend(_historical_summary_lines(dossier.historical_url_intelligence))
    lines.extend(["", "## Top Review Candidates", ""])
    lines.extend(_candidate_lines(dossier.top_review_candidates))
    lines.extend(["", "## Suggested Manual Investigation Plan", ""])
    lines.extend(_guidance_lines(dossier.suggested_manual_investigation_plan))
    lines.extend(["", "## Owner Confirmation Needed", ""])
    if dossier.owner_confirmation_needed:
        lines.extend(f"- {asset}" for asset in dossier.owner_confirmation_needed)
    else:
        lines.append("- None identified")
    lines.extend(["", "## Evidence Collection Template", ""])
    lines.extend(f"- [ ] {item}" for item in dossier.evidence_collection_template)
    lines.append("")
    return "\n".join(lines)


def dossier_to_json(dossier: InvestigationDossier) -> dict[str, object]:
    """Return a deterministic JSON-serializable dossier."""
    return asdict(dossier)


def _load_latest_export(json_exports_dir: Path) -> tuple[Path, dict[str, Any]]:
    """Load the latest existing workspace recon JSON export."""
    export_paths = sorted(
        path
        for path in json_exports_dir.glob("*.json")
        if path.name != "investigation-plan.json"
    )
    if not export_paths:
        raise PlanningError(f"no recon JSON exports found in: {json_exports_dir}")
    exports = [(path, _load_json_mapping(path)) for path in export_paths]
    return max(exports, key=lambda item: (_string(item[1].get("completed_at")), str(item[0])))


def _load_latest_run(database_path: Path, *, target: str) -> dict[str, object]:
    """Read the latest SQLite run summary without creating or mutating the database."""
    if not database_path.is_file():
        raise PlanningError(f"run history database not found: {database_path}")
    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        row = connection.execute(
            """
            SELECT target, run_name, profile, run_status, started_at, completed_at,
                   subdomain_count, live_url_count, url_count
            FROM runs
            WHERE target = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (target,),
        ).fetchone()
    if row is None:
        raise PlanningError(f"run history is empty: {database_path}")
    return {
        "target": str(row[0]),
        "run_name": str(row[1]),
        "profile": str(row[2]),
        "run_status": str(row[3]),
        "started_at": str(row[4]),
        "completed_at": str(row[5]),
        "subdomain_count": int(row[6]),
        "live_url_count": int(row[7]),
        "historical_url_count": int(row[8]),
    }


def _read_scope_entries(scope_file: Path) -> tuple[str, ...]:
    """Read human-maintained scope entries while ignoring blanks and comments."""
    if not scope_file.is_file():
        return ()
    return tuple(
        sorted(
            {
                line.strip().lower().rstrip(".")
                for line in scope_file.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
        )
    )


def _build_candidates(
    export: Mapping[str, Any],
    scope_rules: tuple[str, ...],
) -> list[ReviewCandidate]:
    """Build current observations and historical leads in deterministic priority order."""
    guidance = {
        _string(item.get("url")): item
        for item in _mapping_list(export.get("investigation_guidance"))
    }
    asset_categories = _mapping(export.get("asset_categories"))
    candidates = [
        _current_candidate(item, guidance, asset_categories, scope_rules)
        for item in _mapping_list(export.get("prioritized_assets"))
    ]
    candidates.extend(
        _historical_candidate(item, scope_rules)
        for item in _mapping_list(export.get("historical_url_intelligence"))
    )
    return sorted(
        candidates,
        key=lambda item: (-item.priority, item.observation_type, item.asset),
    )[:25]


def _current_candidate(
    item: Mapping[str, object],
    guidance: Mapping[str, Mapping[str, object]],
    asset_categories: Mapping[str, object],
    scope_rules: tuple[str, ...],
) -> ReviewCandidate:
    """Build one current live-asset review candidate."""
    asset = _string(item.get("url"))
    guidance_item = guidance.get(asset, {})
    category_items = _mapping_list(asset_categories.get(asset))
    categories = sorted({_string(category.get("category")) for category in category_items})
    reasons = tuple(_string_list(item.get("reasons")))
    evidence = tuple(
        value
        for value in (
            "Current live URL observed during recon",
            f"Asset categories: {', '.join(categories)}" if categories else "",
        )
        if value
    )
    return ReviewCandidate(
        asset=asset,
        observation_type=CURRENT_OBSERVATION,
        scope_status=_scope_status(asset, scope_rules),
        priority=_integer(item.get("score")),
        evidence=evidence,
        reason=reasons,
        suggested_checks=_check_titles(guidance_item),
    )


def _historical_candidate(
    item: Mapping[str, object],
    scope_rules: tuple[str, ...],
) -> ReviewCandidate:
    """Build one archived URL lead without implying current reachability."""
    asset = _string(item.get("url"))
    categories = _string_list(item.get("categories"))
    reasons = _string_list(item.get("reasons"))
    sources = _string_list(item.get("sources"))
    return ReviewCandidate(
        asset=asset,
        observation_type=HISTORICAL_LEAD,
        scope_status=_scope_status(asset, scope_rules),
        priority=_historical_priority(categories, _string(item.get("confidence"))),
        evidence=(
            f"Passive archive source(s): {', '.join(sources) or 'unknown'}",
            "Reachability: unverified",
        ),
        reason=tuple(reasons),
        suggested_checks=(
            "Confirm scope and current reachability before any manual review",
        ),
    )


def _historical_priority(categories: list[str], confidence: str) -> int:
    """Assign a small explainable offline review score to historical leads."""
    weights = {
        "Config Indicator": 10,
        "Authentication": 9,
        "Administrative": 8,
        "API": 7,
        "Public Metadata": 6,
        "Source Map": 6,
        "CMS": 5,
        "Redirect Candidate": 4,
    }
    confidence_bonus = {"high": 2, "medium": 1}.get(confidence, 0)
    return max((weights.get(category, 1) for category in categories), default=0) + confidence_bonus


def _scope_status(asset: str, scope_rules: tuple[str, ...]) -> str:
    """Mark an asset in scope only when a configured hostname rule matches."""
    hostname = (urlparse(asset).hostname or asset).lower().rstrip(".")
    for rule in scope_rules:
        rule_hostname = (urlparse(rule).hostname or rule).lower().lstrip("*.").rstrip(".")
        if hostname == rule_hostname or hostname.endswith(f".{rule_hostname}"):
            return IN_SCOPE
    return UNKNOWN_SCOPE


def _new_and_changed_assets(export: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Extract deterministic change evidence already present in the recon export."""
    changes: dict[str, tuple[str, ...]] = {}
    for section in ("asset_changes", "technology_changes", "screenshot_changes"):
        for name, values in sorted(_mapping(export.get(section)).items()):
            changes[f"{section}.{name}"] = tuple(_string_list(values))
    return changes


def _check_titles(guidance_item: Mapping[str, object]) -> tuple[str, ...]:
    """Return concise suggested check titles from exported guidance."""
    return tuple(
        sorted(
            {
                _string(check.get("title"))
                for check in _mapping_list(guidance_item.get("checks"))
                if _string(check.get("title"))
            }
        )
    )


def _collection_quality_lines(statuses: tuple[Mapping[str, object], ...]) -> list[str]:
    """Render collection-quality evidence."""
    if not statuses:
        return ["- No collection quality evidence available"]
    return [
        f"- {status.get('source', 'unknown')} [{status.get('target', 'unknown')}]: "
        f"{status.get('status', 'unknown')} ({status.get('result_count', 0)} results)"
        for status in statuses
    ]


def _changed_asset_lines(changes: Mapping[str, tuple[str, ...]]) -> list[str]:
    """Render new and changed asset evidence."""
    if not changes:
        return ["- No change evidence available"]
    lines: list[str] = []
    for name, values in sorted(changes.items()):
        lines.append(f"- {name}: {len(values)}")
        lines.extend(f"  - {value}" for value in values)
    return lines


def _asset_category_lines(categories: Mapping[str, object]) -> list[str]:
    """Render asset categories from the existing JSON export."""
    assets = _mapping(categories.get("assets"))
    technology_categories = _mapping(categories.get("technology_categories"))
    if not assets and not technology_categories:
        return ["- None identified"]
    lines: list[str] = []
    for asset, raw_matches in sorted(assets.items()):
        labels = sorted(
            {
                _string(match.get("category"))
                for match in _mapping_list(raw_matches)
                if _string(match.get("category"))
            }
        )
        lines.append(f"- {asset}: {', '.join(labels) or 'Uncategorized'}")
    for category, raw_technologies in sorted(technology_categories.items()):
        technologies = ", ".join(sorted(_mapping(raw_technologies)))
        lines.append(f"- Technology category {category}: {technologies or 'None identified'}")
    return lines


def _historical_summary_lines(findings: tuple[Mapping[str, object], ...]) -> list[str]:
    """Render historical category totals without listing the complete lead set."""
    counts: dict[str, int] = {}
    for finding in findings:
        for category in _string_list(finding.get("categories")):
            counts[category] = counts.get(category, 0) + 1
    if not counts:
        return ["- None identified"]
    return [f"- {category}: {count}" for category, count in sorted(counts.items())]


def _candidate_lines(candidates: tuple[ReviewCandidate, ...]) -> list[str]:
    """Render prioritized manual review candidates."""
    if not candidates:
        return ["- None identified"]
    lines: list[str] = []
    for index, candidate in enumerate(candidates, start=1):
        lines.extend(
            [
                f"### {index}. {candidate.asset}",
                "",
                f"- Observation type: {candidate.observation_type}",
                f"- Scope status: {candidate.scope_status}",
                f"- Priority: {candidate.priority}",
                f"- Evidence: {'; '.join(candidate.evidence) or 'None recorded'}",
                f"- Reason: {'; '.join(candidate.reason) or 'None recorded'}",
                "- Suggested checks: "
                + ("; ".join(candidate.suggested_checks) or "Confirm scope before review"),
                "",
            ]
        )
    return lines


def _guidance_lines(guidance: tuple[Mapping[str, object], ...]) -> list[str]:
    """Render exported safe manual guidance concisely."""
    if not guidance:
        return ["- No suggested checks available"]
    lines: list[str] = []
    for item in guidance:
        lines.append(f"### {_string(item.get('url'))}")
        lines.append("")
        for check in _mapping_list(item.get("checks")):
            lines.append(f"- {_string(check.get('category'))}: {_string(check.get('title'))}")
        lines.append("")
    return lines


def _load_json_mapping(path: Path) -> dict[str, Any]:
    """Load one JSON object from disk."""
    try:
        loaded: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlanningError(f"invalid JSON export: {path}") from exc
    if not isinstance(loaded, dict):
        raise PlanningError(f"JSON export must contain an object: {path}")
    return loaded


def _mapping(value: object) -> Mapping[str, object]:
    """Return a mapping or an empty mapping for absent optional evidence."""
    return value if isinstance(value, dict) else {}


def _mapping_list(value: object) -> list[Mapping[str, object]]:
    """Return only mapping items from an optional JSON list."""
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    """Return sorted unique strings from an optional JSON list."""
    return sorted({str(item) for item in value}) if isinstance(value, list) else []


def _string(value: object) -> str:
    """Return a string representation for simple JSON values."""
    return str(value) if value is not None else ""


def _integer(value: object) -> int:
    """Return an integer score for simple JSON values."""
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
