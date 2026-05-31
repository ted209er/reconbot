import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from reconbot import main
from reconbot.config import Config
from reconbot.history import (
    get_previous_screenshots,
    get_previous_technologies,
    list_recent_runs,
    record_live_urls,
    record_run,
    record_subdomains,
    record_technologies,
)
from reconbot.tools.detection import MissingExternalToolsError


@pytest.fixture(autouse=True)
def _use_temp_history_database(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(main, "HISTORY_DATABASE_PATH", tmp_path / "reconbot.db")


def test_run_workflow_calls_wrappers_and_writes_outputs(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    processed_dir = tmp_path / "processed"
    reports_dir = tmp_path / "reports"
    log_file = tmp_path / "logs" / "reconbot.log"
    config_path.write_text(
        (
            f"logging:\n  file: {log_file}\n"
            f"output:\n"
            f"  processed_dir: {processed_dir}\n"
            f"  reports_dir: {reports_dir}\n"
            f"  json_exports_dir: {reports_dir / 'json'}\n"
            "tools:\n"
            "  subfinder:\n"
            "    binary: custom-subfinder\n"
            "    timeout: 10\n"
            "  assetfinder:\n"
            "    binary: custom-assetfinder\n"
            "    timeout: 11\n"
            "  crtsh:\n"
            "    binary: custom-curl\n"
            "    timeout: 12\n"
            "  httpx:\n"
            "    binary: custom-httpx\n"
            "    timeout: 20\n"
            "  gau:\n"
            "    binary: custom-gau\n"
            "    timeout: 30\n"
            "  waybackurls:\n"
            "    binary: custom-waybackurls\n"
            "    timeout: 31\n"
            "  screenshots:\n"
            "    binary: custom-gowitness\n"
            "    timeout: 40\n"
        ),
        encoding="utf-8",
    )

    calls: list[tuple[str, object, str, float]] = []
    validation_calls: list[list[str]] = []

    def fake_validate_required_tools(tool_names: list[str]) -> None:
        validation_calls.append(tool_names)

    def fake_find_subdomains(domain: str, *, binary: str, timeout: float) -> list[str]:
        calls.append(("subfinder", domain, binary, timeout))
        return ["a.example.com", "b.example.com"]

    def fake_find_assetfinder_subdomains(
        domain: str,
        *,
        binary: str,
        timeout: float,
    ) -> list[str]:
        calls.append(("assetfinder", domain, binary, timeout))
        return ["c.example.com"]

    def fake_find_crtsh_subdomains(domain: str, *, binary: str, timeout: float) -> list[str]:
        calls.append(("crtsh", domain, binary, timeout))
        return ["b.example.com", "d.example.com"]

    def fake_find_live_urls(subdomains: list[str], *, binary: str, timeout: float) -> list[str]:
        calls.append(("httpx", subdomains, binary, timeout))
        return ["https://a.example.com", "http://b.example.com"]

    def fake_fingerprint_urls(
        urls: list[str],
        *,
        binary: str,
        timeout: float,
    ) -> dict[str, list[str]]:
        calls.append(("fingerprinting", urls, binary, timeout))
        return {"https://a.example.com": ["Nginx"], "http://b.example.com": ["WordPress"]}

    def fake_find_urls(targets: object, *, binary: str, timeout: float) -> list[str]:
        calls.append(("gau", targets, binary, timeout))
        return ["https://a.example.com/login", "https://b.example.com/archive"]

    def fake_find_wayback_urls(targets: object, *, binary: str, timeout: float) -> list[str]:
        calls.append(("waybackurls", targets, binary, timeout))
        return ["https://c.example.com/old"]

    def fake_capture_screenshots(
        urls: list[str],
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
    ) -> dict[str, Path]:
        calls.append(("screenshots", urls, binary, timeout))
        return {"https://a.example.com": output_dir / "https-a-example-com.png"}

    monkeypatch.setattr(main, "validate_required_tools", fake_validate_required_tools)
    monkeypatch.setattr(main, "find_subdomains", fake_find_subdomains)
    monkeypatch.setattr(main, "find_assetfinder_subdomains", fake_find_assetfinder_subdomains)
    monkeypatch.setattr(main, "find_crtsh_subdomains", fake_find_crtsh_subdomains)
    monkeypatch.setattr(main, "find_live_urls", fake_find_live_urls)
    monkeypatch.setattr(main, "fingerprint_urls", fake_fingerprint_urls)
    monkeypatch.setattr(main, "capture_screenshots", fake_capture_screenshots)
    monkeypatch.setattr(main, "find_historical_urls", fake_find_urls)
    monkeypatch.setattr(main, "find_wayback_urls", fake_find_wayback_urls)

    report = main.run_workflow("example.com", config_path, verbose=False, run_name="daily")

    assert calls == [
        ("subfinder", "example.com", "custom-subfinder", 10.0),
        ("assetfinder", "example.com", "custom-assetfinder", 11.0),
        ("crtsh", "example.com", "custom-curl", 12.0),
        (
            "httpx",
            ["a.example.com", "b.example.com", "c.example.com", "d.example.com"],
            "custom-httpx",
            20.0,
        ),
        ("fingerprinting", ["https://a.example.com", "http://b.example.com"], "custom-httpx", 20.0),
        (
            "screenshots",
            ["https://a.example.com", "http://b.example.com"],
            "custom-gowitness",
            40.0,
        ),
        ("gau", ["a.example.com", "b.example.com"], "custom-gau", 30.0),
        ("waybackurls", ["a.example.com", "b.example.com"], "custom-waybackurls", 31.0),
    ]
    assert validation_calls == [
        [
            "custom-subfinder",
            "custom-assetfinder",
            "custom-curl",
            "custom-httpx",
            "custom-gau",
            "custom-waybackurls",
            "custom-gowitness",
        ]
    ]
    assert report.target.domain == "example.com"
    assert [result.name for result in report.results] == ["subfinder", "httpx", "gau"]
    assert (processed_dir / "subdomains.txt").read_text(encoding="utf-8") == (
        "a.example.com\nb.example.com\nc.example.com\nd.example.com\n"
    )
    assert (processed_dir / "live_urls.txt").read_text(encoding="utf-8") == (
        "https://a.example.com\nhttp://b.example.com\n"
    )
    assert (processed_dir / "historical_urls.txt").read_text(encoding="utf-8") == (
        "https://a.example.com/login\nhttps://b.example.com/archive\nhttps://c.example.com/old\n"
    )
    assert (processed_dir / "technologies.txt").read_text(encoding="utf-8") == (
        "http://b.example.com\tWordPress\nhttps://a.example.com\tNginx\n"
    )
    report_text = (reports_dir / "example.com.md").read_text(encoding="utf-8")
    assert "- Target domain: `example.com`" in report_text
    assert "- Subdomain count: 4" in report_text
    assert "- assetfinder: 1" in report_text
    assert "- crtsh: 2" in report_text
    assert "- subfinder: 2" in report_text
    assert "- waybackurls: 1" in report_text
    assert "- Live host count: 2" in report_text
    assert "- URL count: 3" in report_text
    assert "- Screenshots captured: 1" in report_text
    assert "- New screenshot targets: 1" in report_text
    assert "+ https://a.example.com" in report_text
    assert "## Technology Categories" in report_text
    assert "Infrastructure:" in report_text
    assert "CMS:" in report_text
    assert "- WordPress (1)" in report_text
    assert "## High Interest Assets" in report_text
    assert "1. https://a.example.com" in report_text
    assert "   - New live URL" in report_text
    history = list_recent_runs(database_path=main.HISTORY_DATABASE_PATH)
    assert len(history) == 1
    assert history[0].target == "example.com"
    assert history[0].run_name == "daily"
    assert history[0].profile == "standard"
    assert history[0].subdomain_count == 4
    assert history[0].live_url_count == 2
    assert history[0].url_count == 3
    previous_technologies = get_previous_technologies(
        target="example.com",
        database_path=main.HISTORY_DATABASE_PATH,
    )
    assert previous_technologies == [
        "Nginx",
        "WordPress",
    ]
    previous_screenshots = get_previous_screenshots(
        target="example.com",
        database_path=main.HISTORY_DATABASE_PATH,
    )
    assert previous_screenshots == {
        "https://a.example.com": (
            reports_dir / "screenshots" / "example-com" / "https-a-example-com.png"
        )
    }
    json_export = json.loads((reports_dir / "json" / "example-com.json").read_text())
    assert json_export["target"] == "example.com"
    assert json_export["run_name"] == "daily"
    assert json_export["profile"] == "standard"
    assert json_export["counts"]["screenshots"] == 1
    assert json_export["technology_categories"] == {
        "CMS": {"WordPress": 1},
        "Infrastructure": {"Nginx": 1},
    }
    assert json_export["subdomains"] == [
        "a.example.com",
        "b.example.com",
        "c.example.com",
        "d.example.com",
    ]
    assert json_export["discovery_sources"]["subdomains"]["crtsh"] == 2
    assert json_export["screenshot_changes"]["added_screenshots"] == ["https://a.example.com"]
    assert json_export["prioritized_assets"][0]["url"] == "https://a.example.com"
    assert json_export["prioritized_assets"][0]["score"] == 15


def test_run_workflow_prints_startup_progress_and_summary(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    processed_dir = tmp_path / "processed"
    reports_dir = tmp_path / "reports"
    config_path.write_text(
        (
            f"logging:\n  file: {tmp_path / 'reconbot.log'}\n"
            f"output:\n  processed_dir: {processed_dir}\n  reports_dir: {reports_dir}\n"
            "tools:\n"
            "  subfinder:\n"
            "    enabled: false\n"
            "  assetfinder:\n"
            "    enabled: false\n"
            "  crtsh:\n"
            "    enabled: false\n"
            "  httpx:\n"
            "    enabled: false\n"
            "  gau:\n"
            "    enabled: false\n"
            "  waybackurls:\n"
            "    enabled: false\n"
            "  screenshots:\n"
            "    enabled: false\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(main, "validate_required_tools", lambda tool_names: None)

    main.run_workflow("example.com", config_path, verbose=False)

    output = capsys.readouterr().out
    assert "Reconbot" in output
    assert "Target: example.com" in output
    assert "Profile: standard" in output
    assert "- subfinder: disabled, binary=subfinder, timeout=120s" in output
    assert "Complete" in output
    assert f"Report: {reports_dir / 'example.com.md'}" in output
    assert f"- {processed_dir / 'subdomains.txt'}" in output


def test_run_workflow_skips_disabled_tools(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    processed_dir = tmp_path / "processed"
    config_path.write_text(
        (
            f"logging:\n  file: {tmp_path / 'reconbot.log'}\n"
            f"output:\n  processed_dir: {processed_dir}\n  reports_dir: {tmp_path / 'reports'}\n"
            "tools:\n"
            "  subfinder:\n"
            "    enabled: false\n"
            "  assetfinder:\n"
            "    enabled: false\n"
            "  crtsh:\n"
            "    enabled: false\n"
            "  httpx:\n"
            "    enabled: false\n"
            "  gau:\n"
            "    enabled: false\n"
            "  waybackurls:\n"
            "    enabled: false\n"
            "  screenshots:\n"
            "    enabled: false\n"
        ),
        encoding="utf-8",
    )
    validation_calls: list[list[str]] = []

    def fake_validate_required_tools(tool_names: list[str]) -> None:
        validation_calls.append(tool_names)

    def fail_if_called(*args: object, **kwargs: object) -> list[str]:
        raise AssertionError("disabled tool wrapper should not run")

    monkeypatch.setattr(main, "validate_required_tools", fake_validate_required_tools)
    monkeypatch.setattr(main, "find_subdomains", fail_if_called)
    monkeypatch.setattr(main, "find_assetfinder_subdomains", fail_if_called)
    monkeypatch.setattr(main, "find_crtsh_subdomains", fail_if_called)
    monkeypatch.setattr(main, "find_live_urls", fail_if_called)
    monkeypatch.setattr(main, "fingerprint_urls", fail_if_called)
    monkeypatch.setattr(main, "capture_screenshots", fail_if_called)
    monkeypatch.setattr(main, "find_historical_urls", fail_if_called)
    monkeypatch.setattr(main, "find_wayback_urls", fail_if_called)

    report = main.run_workflow("example.com", config_path, verbose=False)

    assert validation_calls == [[]]
    assert [result.output for result in report.results] == ["", "", ""]
    assert (processed_dir / "subdomains.txt").read_text(encoding="utf-8") == ""
    assert (processed_dir / "live_urls.txt").read_text(encoding="utf-8") == ""
    assert (processed_dir / "historical_urls.txt").read_text(encoding="utf-8") == ""
    assert (processed_dir / "technologies.txt").read_text(encoding="utf-8") == ""


def test_run_workflow_skips_json_export_when_disabled(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    reports_dir = tmp_path / "reports"
    config_path.write_text(
        (
            f"logging:\n  file: {tmp_path / 'reconbot.log'}\n"
            f"output:\n"
            f"  processed_dir: {tmp_path / 'processed'}\n"
            f"  reports_dir: {reports_dir}\n"
            f"  json_exports_dir: {reports_dir / 'json'}\n"
            "  write_json: false\n"
            "tools:\n"
            "  subfinder:\n"
            "    enabled: false\n"
            "  assetfinder:\n"
            "    enabled: false\n"
            "  crtsh:\n"
            "    enabled: false\n"
            "  httpx:\n"
            "    enabled: false\n"
            "  gau:\n"
            "    enabled: false\n"
            "  waybackurls:\n"
            "    enabled: false\n"
            "  screenshots:\n"
            "    enabled: false\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(main, "validate_required_tools", lambda tool_names: None)

    main.run_workflow("example.com", config_path, verbose=False)

    assert not (reports_dir / "json" / "example-com.json").exists()


def test_run_workflow_reports_diff_from_previous_run(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    reports_dir = tmp_path / "reports"
    config_path.write_text(
        (
            f"logging:\n  file: {tmp_path / 'reconbot.log'}\n"
            f"output:\n  processed_dir: {tmp_path / 'processed'}\n  reports_dir: {reports_dir}\n"
            "tools:\n"
            "  subfinder:\n"
            "    enabled: true\n"
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
            "    enabled: false\n"
        ),
        encoding="utf-8",
    )
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    previous_run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=2,
        live_url_count=1,
        url_count=0,
        database_path=main.HISTORY_DATABASE_PATH,
    )
    record_subdomains(
        run_id=previous_run_id,
        subdomains=["api.example.com", "old.example.com"],
        database_path=main.HISTORY_DATABASE_PATH,
    )
    record_live_urls(
        run_id=previous_run_id,
        urls=["https://old.example.com"],
        database_path=main.HISTORY_DATABASE_PATH,
    )
    record_technologies(
        run_id=previous_run_id,
        technologies={"https://old.example.com": ["Drupal"]},
        database_path=main.HISTORY_DATABASE_PATH,
    )

    monkeypatch.setattr(main, "validate_required_tools", lambda tool_names: None)
    monkeypatch.setattr(
        main,
        "find_subdomains",
        lambda domain, *, binary, timeout: ["api.example.com", "beta.example.com"],
    )
    monkeypatch.setattr(
        main,
        "find_live_urls",
        lambda subdomains, *, binary, timeout: ["https://beta.example.com"],
    )
    monkeypatch.setattr(
        main,
        "fingerprint_urls",
        lambda urls, *, binary, timeout: {"https://beta.example.com": ["FastAPI"]},
    )

    main.run_workflow("example.com", config_path, verbose=False)

    report_text = (reports_dir / "example.com.md").read_text(encoding="utf-8")
    assert "- Added subdomains: 1" in report_text
    assert "- Removed subdomains: 1" in report_text
    assert "- Added live URLs: 1" in report_text
    assert "- Removed live URLs: 1" in report_text
    assert "+ beta.example.com" in report_text
    assert "- old.example.com" in report_text
    assert "+ https://beta.example.com" in report_text
    assert "- https://old.example.com" in report_text
    assert "- FastAPI (1)" in report_text
    assert "## Technology Categories" in report_text
    assert "Framework:" in report_text
    assert "- Added technologies: 1" in report_text
    assert "- Removed technologies: 1" in report_text
    assert "+ FastAPI" in report_text
    assert "- Drupal" in report_text


def test_run_workflow_validates_required_tools(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"logging:\n  file: {tmp_path / 'reconbot.log'}\n",
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def fake_validate_required_tools(tool_names: list[str]) -> None:
        calls.append(tool_names)
        raise RuntimeError("missing tools")

    monkeypatch.setattr(main, "validate_required_tools", fake_validate_required_tools)

    with pytest.raises(RuntimeError, match="missing tools"):
        main.run_workflow("example.com", config_path, verbose=False)

    assert calls == [
        ["subfinder", "assetfinder", "curl", "httpx", "gau", "waybackurls", "gowitness"]
    ]


def test_load_runtime_config_uses_custom_config_when_supplied(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("logging:\n  file: custom.log\n", encoding="utf-8")

    config, effective_path, using_packaged_config = main._load_runtime_config(config_path)

    assert effective_path == config_path
    assert using_packaged_config is False
    assert config["logging"]["file"] == "custom.log"


def test_run_workflow_uses_packaged_config_when_config_is_omitted(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    default_config_path = tmp_path / "packaged-default.yaml"
    workspace = tmp_path / "workspace"
    packaged_config: Config = {
        "logging": {"file": str(tmp_path / "reconbot.log")},
        "tools": {
            "subfinder": {"enabled": False},
            "assetfinder": {"enabled": False},
            "crtsh": {"enabled": False},
            "httpx": {"enabled": False},
            "gau": {"enabled": False},
            "waybackurls": {"enabled": False},
            "screenshots": {"enabled": False},
        },
    }

    monkeypatch.setattr(main, "load_default_config", lambda: packaged_config)
    monkeypatch.setattr(main, "get_default_config_path", lambda: default_config_path)
    monkeypatch.setattr(main, "validate_required_tools", lambda tool_names: None)

    main.run_workflow(
        "example.com",
        None,
        verbose=False,
        workspace_path=workspace,
    )

    output = capsys.readouterr().out
    assert "Using packaged default config" in output
    assert f"Workspace: {workspace.resolve()}" in output
    assert (workspace / "reports" / "example.com.md").is_file()
    assert (workspace / "data" / "reconbot.db").is_file()
    assert not (tmp_path / "reports" / "example.com.md").exists()


def test_main_prints_missing_binary_errors(
    monkeypatch: MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_workflow(
        domain: str,
        config_path: Path,
        verbose: bool,
        run_name: str = "",
        workspace_path: Path | None = None,
        profile: object = "standard",
    ) -> None:
        raise MissingExternalToolsError("Missing required external tool(s): subfinder.")

    monkeypatch.setattr(main, "run_workflow", fake_run_workflow)

    exit_code = main.main(["--domain", "example.com"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Error: Missing required external tool(s): subfinder." in captured.err


def test_hosts_from_urls_deduplicates_and_sorts() -> None:
    urls = ["https://b.example.com/path", "http://a.example.com", "https://b.example.com"]

    assert main._hosts_from_urls(urls) == ["a.example.com", "b.example.com"]
