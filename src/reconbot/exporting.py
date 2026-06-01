"""Structured JSON export helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from reconbot.collection_status import CollectionStatus, RunCompleteness
from reconbot.guidance import AssetGuidance
from reconbot.models import ReconReport
from reconbot.prioritization import PrioritizedAsset
from reconbot.screenshots import ScreenshotDiagnostic
from reconbot.technology_categories import CATEGORY_ORDER, AssetCategory
from reconbot.url_intelligence import (
    HISTORICAL_OBSERVATION_TYPE,
    HISTORICAL_REACHABILITY,
    HistoricalUrlFinding,
)


def build_json_export(
    *,
    report: ReconReport,
    run_name: str,
    output_files: Mapping[str, Path],
    report_path: Path,
    subdomains: list[str],
    live_urls: list[str],
    historical_urls: list[str],
    technology_summary: Mapping[str, int],
    technology_categories: Mapping[str, Mapping[str, int]],
    technology_category_summary: Mapping[str, int],
    technology_diff: Mapping[str, list[str]],
    screenshots: Mapping[str, Path],
    screenshot_diff: Mapping[str, list[str]],
    prioritized_assets: list[PrioritizedAsset],
    subdomain_sources: Mapping[str, int],
    historical_url_sources: Mapping[str, int],
    workspace_path: Path | None = None,
    profile: str = "standard",
    asset_categories: Mapping[str, list[AssetCategory]] | None = None,
    asset_category_summary: Mapping[str, int] | None = None,
    investigation_guidance: list[AssetGuidance] | None = None,
    guidance_summary: Mapping[str, int] | None = None,
    collection_statuses: list[CollectionStatus] | None = None,
    run_status: RunCompleteness = RunCompleteness.COMPLETE,
    screenshot_diagnostics: list[ScreenshotDiagnostic] | None = None,
    historical_url_intelligence: list[HistoricalUrlFinding] | None = None,
) -> dict[str, Any]:
    """Build a deterministic JSON-serializable export."""
    screenshot_paths = {url: str(path) for url, path in sorted(screenshots.items())}
    diagnostic_items = screenshot_diagnostics or []
    return {
        "target": report.target.domain,
        "run_name": run_name,
        "profile": profile,
        "run_status": run_status.value,
        "started_at": report.started_at.isoformat(),
        "completed_at": report.finished_at.isoformat() if report.finished_at else None,
        "workspace": str(workspace_path) if workspace_path is not None else None,
        "report_path": str(report_path),
        "output_paths": _stringify_paths(output_files),
        "counts": {
            "subdomains": len(subdomains),
            "live_urls": len(live_urls),
            "historical_urls": len(historical_urls),
            "technologies": len(technology_summary),
            "screenshots": len(screenshots),
        },
        "subdomains": sorted(subdomains),
        "live_urls": sorted(live_urls),
        "historical_urls": sorted(historical_urls),
        "historical_url_intelligence": _historical_url_intelligence(
            historical_url_intelligence or []
        ),
        "technology_summary": dict(sorted(technology_summary.items())),
        "technology_categories": _nested_mapping(technology_categories),
        "technology_category_summary": dict(technology_category_summary),
        "asset_categories": _asset_categories(asset_categories or {}),
        "asset_category_summary": dict(asset_category_summary or {}),
        "investigation_guidance": _investigation_guidance(investigation_guidance or []),
        "investigation_guidance_summary": dict(guidance_summary or {}),
        "collection_status": _collection_statuses(collection_statuses or []),
        "technology_changes": _sorted_change_lists(technology_diff),
        "screenshot_paths": screenshot_paths,
        "screenshot_status": {
            diagnostic.url: diagnostic.status.value
            for diagnostic in sorted(diagnostic_items, key=lambda item: item.url)
        },
        "screenshot_error": {
            diagnostic.url: diagnostic.error
            for diagnostic in sorted(diagnostic_items, key=lambda item: item.url)
            if diagnostic.error
        },
        "screenshot_changes": _sorted_change_lists(screenshot_diff),
        "prioritized_assets": _prioritized_assets(prioritized_assets),
        "discovery_sources": {
            "subdomains": dict(sorted(subdomain_sources.items())),
            "historical_urls": dict(sorted(historical_url_sources.items())),
        },
    }


def write_json_export(export: Mapping[str, Any], export_path: Path) -> Path:
    """Write a deterministic JSON export to disk."""
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(export, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return export_path


def _stringify_paths(paths: Mapping[str, Path]) -> dict[str, str]:
    """Return output paths as sorted strings."""
    return {name: str(path) for name, path in sorted(paths.items())}


def _sorted_change_lists(changes: Mapping[str, list[str]]) -> dict[str, list[str]]:
    """Return sorted change lists with stable keys."""
    return {name: sorted(values) for name, values in sorted(changes.items())}


def _prioritized_assets(assets: list[PrioritizedAsset]) -> list[dict[str, Any]]:
    """Return prioritized assets as JSON-serializable dictionaries."""
    return [
        {
            "url": asset.url,
            "score": asset.score,
            "reasons": sorted(asset.reasons),
        }
        for asset in assets
    ]


def _nested_mapping(values: Mapping[str, Mapping[str, int]]) -> dict[str, dict[str, int]]:
    """Return nested mappings with deterministic ordering."""
    nested: dict[str, dict[str, int]] = {}
    for outer_key in CATEGORY_ORDER:
        if outer_key in values:
            nested[outer_key] = dict(sorted(values[outer_key].items()))
    for outer_key, inner_values in sorted(values.items()):
        if outer_key not in nested:
            nested[outer_key] = dict(sorted(inner_values.items()))
    return nested


def _asset_categories(
    assets: Mapping[str, list[AssetCategory]],
) -> dict[str, list[dict[str, object]]]:
    """Return deterministic JSON-serializable asset categories."""
    return {
        url: [
            {
                "category": match.category,
                "confidence": match.confidence.value,
                "indicators": list(match.indicators),
            }
            for match in matches
        ]
        for url, matches in sorted(assets.items())
    }


def _investigation_guidance(guidance: list[AssetGuidance]) -> list[dict[str, object]]:
    """Return deterministic JSON-serializable investigation guidance."""
    return [
        {
            "url": asset.url,
            "reasons": list(asset.reasons),
            "checks": [
                {
                    "category": check.category,
                    "title": check.title,
                    "why_it_matters": check.why_it_matters,
                    "safe_manual_approach": check.safe_manual_approach,
                    "evidence_to_collect": check.evidence_to_collect,
                    "safety_note": check.safety_note,
                }
                for check in asset.checks
            ],
        }
        for asset in guidance
    ]


def _collection_statuses(statuses: list[CollectionStatus]) -> list[dict[str, object]]:
    """Return deterministic JSON-serializable collection quality evidence."""
    return [
        {
            "source": status.source,
            "target": status.target,
            "status": status.status.value,
            "result_count": status.result_count,
            "return_code": status.return_code,
            "error_summary": status.error_summary,
        }
        for status in sorted(
            statuses,
            key=lambda item: (item.source, item.target, item.status.value),
        )
    ]


def _historical_url_intelligence(
    findings: list[HistoricalUrlFinding],
) -> list[dict[str, object]]:
    """Return full deterministic historical lead intelligence."""
    return [
        {
            "observation_type": HISTORICAL_OBSERVATION_TYPE,
            "reachability": HISTORICAL_REACHABILITY,
            "url": finding.url,
            "hostname": finding.hostname,
            "path": finding.path,
            "query_keys": list(finding.query_keys),
            "categories": list(finding.categories),
            "sources": list(finding.sources),
            "confidence": finding.confidence.value,
            "reasons": list(finding.reasons),
        }
        for finding in sorted(findings, key=lambda item: item.url)
    ]
