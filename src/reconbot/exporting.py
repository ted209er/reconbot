"""Structured JSON export helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from reconbot.models import ReconReport
from reconbot.prioritization import PrioritizedAsset
from reconbot.technology_categories import CATEGORY_ORDER


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
) -> dict[str, Any]:
    """Build a deterministic JSON-serializable export."""
    screenshot_paths = {url: str(path) for url, path in sorted(screenshots.items())}
    return {
        "target": report.target.domain,
        "run_name": run_name,
        "profile": profile,
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
        "technology_summary": dict(sorted(technology_summary.items())),
        "technology_categories": _nested_mapping(technology_categories),
        "technology_category_summary": dict(technology_category_summary),
        "technology_changes": _sorted_change_lists(technology_diff),
        "screenshot_paths": screenshot_paths,
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
