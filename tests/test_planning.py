import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from reconbot import main
from reconbot.history import record_run
from reconbot.planning import (
    CURRENT_OBSERVATION,
    HISTORICAL_LEAD,
    IN_SCOPE,
    UNKNOWN_SCOPE,
    DossierPaths,
    PlanningError,
    generate_review_dossier,
)
from reconbot.workspaces import ensure_workspace


def test_generate_review_dossier_combines_existing_workspace_evidence(tmp_path: Path) -> None:
    workspace = tmp_path / "engagement"
    paths = ensure_workspace(workspace)
    paths.scope_file.write_text("example.com\n", encoding="utf-8")
    started_at = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    record_run(
        target="example.com",
        run_name="daily",
        run_status="PARTIAL",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=1,
        live_url_count=1,
        url_count=2,
        database_path=paths.database_path,
    )
    export_path = paths.json_exports_dir / "example-com.json"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(
            {
                "target": "example.com",
                "completed_at": (started_at + timedelta(seconds=5)).isoformat(),
                "run_status": "PARTIAL",
                "collection_status": [
                    {
                        "source": "gau",
                        "target": "example.com",
                        "status": "FAILED",
                        "result_count": 0,
                    }
                ],
                "asset_changes": {"added_live_urls": ["https://admin.example.com"]},
                "asset_categories": {
                    "https://admin.example.com": [{"category": "Administrative"}]
                },
                "technology_categories": {"Infrastructure": {"Nginx": 1}},
                "prioritized_assets": [
                    {
                        "url": "https://admin.example.com",
                        "score": 8,
                        "reasons": ["New live URL", "Administrative URL keyword"],
                    }
                ],
                "investigation_guidance": [
                    {
                        "url": "https://admin.example.com",
                        "checks": [
                            {"category": "Administrative", "title": "Admin exposure review"}
                        ],
                    }
                ],
                "historical_url_intelligence": [
                    {
                        "url": "https://legacy.example.com/settings.yml",
                        "categories": ["Config Indicator"],
                        "sources": ["waybackurls"],
                        "confidence": "high",
                        "reasons": ["Config Indicator: file suffix: .yml"],
                    },
                    {
                        "url": "https://outside.example.net/login",
                        "categories": ["Authentication"],
                        "sources": ["gau"],
                        "confidence": "medium",
                        "reasons": ["Authentication: keyword: login"],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    dossier_paths = generate_review_dossier(workspace)

    markdown = dossier_paths.markdown.read_text(encoding="utf-8")
    dossier_json = json.loads(dossier_paths.json.read_text(encoding="utf-8"))
    assert dossier_paths.markdown == paths.reports_dir / "investigation-plan.md"
    assert dossier_paths.json == paths.reports_dir / "investigation-plan.json"
    for heading in (
        "Authorization Reminder",
        "Scope Summary",
        "Collection Quality",
        "New and Changed Assets",
        "Asset Categories",
        "Historical URL Intelligence",
        "Top Review Candidates",
        "Suggested Manual Investigation Plan",
        "Owner Confirmation Needed",
        "Evidence Collection Template",
    ):
        assert f"## {heading}" in markdown
    assert "- Reachability: unverified" in markdown
    assert "Archive presence is not evidence that a URL remains reachable." in markdown
    assert "- Technology category Infrastructure: Nginx" in markdown
    assert "https://outside.example.net/login" in dossier_json["owner_confirmation_needed"]
    candidates = {
        candidate["asset"]: candidate for candidate in dossier_json["top_review_candidates"]
    }
    assert candidates["https://legacy.example.com/settings.yml"]["observation_type"] == (
        HISTORICAL_LEAD
    )
    assert candidates["https://legacy.example.com/settings.yml"]["scope_status"] == IN_SCOPE
    assert candidates["https://admin.example.com"]["observation_type"] == CURRENT_OBSERVATION
    assert candidates["https://admin.example.com"]["suggested_checks"] == [
        "Admin exposure review"
    ]
    assert candidates["https://outside.example.net/login"]["scope_status"] == UNKNOWN_SCOPE


def test_generate_review_dossier_requires_existing_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "empty"
    ensure_workspace(workspace)

    with pytest.raises(PlanningError, match="no recon JSON exports"):
        generate_review_dossier(workspace)


def test_main_plan_generates_dossier_without_running_recon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "engagement"
    expected_markdown = workspace / "reports" / "investigation-plan.md"
    expected_json = workspace / "reports" / "investigation-plan.json"
    calls: list[Path] = []

    def fake_generate_review_dossier(workspace_path: Path) -> DossierPaths:
        calls.append(workspace_path)
        return DossierPaths(markdown=expected_markdown, json=expected_json)

    monkeypatch.setattr(main, "generate_review_dossier", fake_generate_review_dossier)

    def fail_run_workflow(*args: object, **kwargs: object) -> None:
        pytest.fail("plan command must not run recon")

    monkeypatch.setattr(main, "run_workflow", fail_run_workflow)

    exit_code = main.main(["plan", "--workspace", str(workspace)])

    assert exit_code == 0
    assert calls == [workspace]
    output = capsys.readouterr().out
    assert str(expected_markdown) in output
    assert str(expected_json) in output
