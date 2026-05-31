import json
from pathlib import Path

from pytest import MonkeyPatch

from reconbot import main
from reconbot.fingerprinting import PassiveAssetMetadata
from reconbot.history import list_recent_runs
from reconbot.workspaces import ensure_workspace, resolve_workspace, workspace_paths


def test_resolve_workspace_expands_and_resolves(tmp_path: Path) -> None:
    workspace = tmp_path / "engagement"

    assert resolve_workspace(workspace) == workspace.resolve()
    assert resolve_workspace(None) is None


def test_workspace_paths_are_deterministic(tmp_path: Path) -> None:
    workspace = tmp_path / "engagement"
    paths = workspace_paths(workspace)

    assert paths.root == workspace.resolve()
    assert paths.data_dir == workspace.resolve() / "data"
    assert paths.processed_dir == workspace.resolve() / "data" / "processed"
    assert paths.reports_dir == workspace.resolve() / "reports"
    assert paths.screenshots_dir == workspace.resolve() / "screenshots"
    assert paths.findings_dir == workspace.resolve() / "findings"
    assert paths.notes_dir == workspace.resolve() / "notes"
    assert paths.scope_file == workspace.resolve() / "scope.txt"
    assert paths.database_path == workspace.resolve() / "data" / "reconbot.db"
    assert paths.json_exports_dir == workspace.resolve() / "reports" / "json"


def test_ensure_workspace_creates_standard_layout(tmp_path: Path) -> None:
    paths = ensure_workspace(tmp_path / "engagement")

    assert paths.data_dir.is_dir()
    assert paths.reports_dir.is_dir()
    assert paths.screenshots_dir.is_dir()
    assert paths.findings_dir.is_dir()
    assert paths.notes_dir.is_dir()
    assert paths.scope_file.is_file()


def test_run_workflow_writes_artifacts_to_workspace(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    workspace = tmp_path / "workspace"
    config_path.write_text(
        (
            f"logging:\n  file: {tmp_path / 'reconbot.log'}\n"
            "tools:\n"
            "  subfinder:\n"
            "    enabled: false\n"
            "  assetfinder:\n"
            "    enabled: false\n"
            "  crtsh:\n"
            "    enabled: false\n"
            "  httpx:\n"
            "    enabled: true\n"
            "  gau:\n"
            "    enabled: false\n"
            "  waybackurls:\n"
            "    enabled: false\n"
            "  screenshots:\n"
            "    enabled: true\n"
        ),
        encoding="utf-8",
    )

    def fake_find_live_urls(
        subdomains: list[str],
        *,
        binary: str,
        timeout: float,
    ) -> list[str]:
        return ["https://app.example.com"]

    def fake_fingerprint_urls(
        urls: list[str],
        *,
        binary: str,
        timeout: float,
        metadata: dict[str, PassiveAssetMetadata] | None = None,
    ) -> dict[str, list[str]]:
        return {"https://app.example.com": ["Nginx"]}

    def fake_capture_screenshots(
        urls: list[str],
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = output_dir / "https-app-example-com.png"
        screenshot_path.write_text("screenshot", encoding="utf-8")
        return {"https://app.example.com": screenshot_path}

    monkeypatch.setattr(main, "validate_required_tools", lambda tool_names: None)
    monkeypatch.setattr(main, "find_live_urls", fake_find_live_urls)
    monkeypatch.setattr(main, "fingerprint_urls", fake_fingerprint_urls)
    monkeypatch.setattr(main, "capture_screenshots", fake_capture_screenshots)

    main.run_workflow(
        "example.com",
        config_path,
        verbose=False,
        run_name="workspace-test",
        workspace_path=workspace,
    )

    resolved_workspace = workspace.resolve()
    report_path = resolved_workspace / "reports" / "example.com.md"
    json_path = resolved_workspace / "reports" / "json" / "example-com.json"
    database_path = resolved_workspace / "data" / "reconbot.db"
    screenshot_path = (
        resolved_workspace / "screenshots" / "example-com" / "https-app-example-com.png"
    )

    assert (resolved_workspace / "scope.txt").is_file()
    assert (resolved_workspace / "findings").is_dir()
    assert (resolved_workspace / "notes").is_dir()
    assert (resolved_workspace / "data" / "processed" / "live_urls.txt").read_text(
        encoding="utf-8"
    ) == "https://app.example.com\n"
    assert report_path.is_file()
    assert f"    {resolved_workspace}" in report_path.read_text(encoding="utf-8")
    assert screenshot_path.read_text(encoding="utf-8") == "screenshot"
    assert database_path.is_file()

    history = list_recent_runs(database_path=database_path)
    assert len(history) == 1
    assert history[0].run_name == "workspace-test"

    json_export = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_export["workspace"] == str(resolved_workspace)
    assert json_export["report_path"] == str(report_path)
    assert json_export["screenshot_paths"] == {
        "https://app.example.com": str(screenshot_path)
    }
