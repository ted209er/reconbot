from pathlib import Path

import pytest
from pytest import MonkeyPatch

from reconbot import main


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
            f"output:\n  processed_dir: {processed_dir}\n  reports_dir: {reports_dir}\n"
        ),
        encoding="utf-8",
    )

    calls: list[tuple[str, object]] = []

    def fake_find_subdomains(domain: str) -> list[str]:
        calls.append(("subfinder", domain))
        return ["a.example.com", "b.example.com"]

    def fake_find_live_urls(subdomains: list[str]) -> list[str]:
        calls.append(("httpx", subdomains))
        return ["https://a.example.com", "http://b.example.com"]

    def fake_find_urls(targets: object) -> list[str]:
        calls.append(("gau", targets))
        return ["https://a.example.com/login", "https://b.example.com/archive"]

    monkeypatch.setattr(main, "validate_required_tools", lambda tool_names: None)
    monkeypatch.setattr(main, "find_subdomains", fake_find_subdomains)
    monkeypatch.setattr(main, "find_live_urls", fake_find_live_urls)
    monkeypatch.setattr(main, "find_historical_urls", fake_find_urls)

    report = main.run_workflow("example.com", config_path, verbose=False)

    assert calls == [
        ("subfinder", "example.com"),
        ("httpx", ["a.example.com", "b.example.com"]),
        ("gau", ["a.example.com", "b.example.com"]),
    ]
    assert report.target.domain == "example.com"
    assert [result.name for result in report.results] == ["subfinder", "httpx", "gau"]
    assert (processed_dir / "subdomains.txt").read_text(encoding="utf-8") == (
        "a.example.com\nb.example.com\n"
    )
    assert (processed_dir / "live_urls.txt").read_text(encoding="utf-8") == (
        "https://a.example.com\nhttp://b.example.com\n"
    )
    assert (processed_dir / "historical_urls.txt").read_text(encoding="utf-8") == (
        "https://a.example.com/login\nhttps://b.example.com/archive\n"
    )
    report_text = (reports_dir / "example.com.md").read_text(encoding="utf-8")
    assert "- Target domain: `example.com`" in report_text
    assert "- Subdomain count: 2" in report_text
    assert "- Live host count: 2" in report_text
    assert "- URL count: 2" in report_text


def test_run_workflow_validates_required_tools(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"logging:\n  file: {tmp_path / 'reconbot.log'}\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, ...]] = []

    def fake_validate_required_tools(tool_names: tuple[str, ...]) -> None:
        calls.append(tool_names)
        raise RuntimeError("missing tools")

    monkeypatch.setattr(main, "validate_required_tools", fake_validate_required_tools)

    with pytest.raises(RuntimeError, match="missing tools"):
        main.run_workflow("example.com", config_path, verbose=False)

    assert calls == [main.REQUIRED_EXTERNAL_TOOLS]


def test_hosts_from_urls_deduplicates_and_sorts() -> None:
    urls = ["https://b.example.com/path", "http://a.example.com", "https://b.example.com"]

    assert main._hosts_from_urls(urls) == ["a.example.com", "b.example.com"]
