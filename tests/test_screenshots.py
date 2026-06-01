from pathlib import Path

from pytest import MonkeyPatch

from reconbot import screenshots
from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.models import ToolResult


def test_capture_screenshot_calls_gowitness(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, Path, str, float]] = []

    def fake_run_screenshot_capture(
        target: str,
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        calls.append((target, output_dir, binary, timeout))
        return ToolResult(name="gowitness", success=True)

    monkeypatch.setattr(screenshots, "run_screenshot_capture", fake_run_screenshot_capture)

    statuses: list[CollectionStatus] = []
    result = screenshots.capture_screenshot(
        "https://admin.example.com/login",
        output_dir=tmp_path,
        binary="custom-gowitness",
        timeout=30,
        collection_statuses=statuses,
    )

    assert result == tmp_path / "https-admin-example-com-login.png"
    assert calls == [
        ("https://admin.example.com/login", tmp_path, "custom-gowitness", 30),
    ]
    assert statuses[0].source == "gowitness"
    assert statuses[0].status == CollectionState.SUCCESS


def test_capture_screenshot_returns_none_on_failure(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_run_screenshot_capture(
        target: str,
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        return ToolResult(name="gowitness", success=False, return_code=1)

    monkeypatch.setattr(screenshots, "run_screenshot_capture", fake_run_screenshot_capture)

    assert screenshots.capture_screenshot("https://example.com", output_dir=tmp_path) is None


def test_capture_screenshots_skips_blank_urls(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    def fake_capture_screenshot(
        url: str,
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
        collection_statuses: object = None,
    ) -> Path:
        return output_dir / f"{url}.png"

    monkeypatch.setattr(screenshots, "capture_screenshot", fake_capture_screenshot)

    result = screenshots.capture_screenshots(["https://a.example.com", "  "], output_dir=tmp_path)

    assert result == {"https://a.example.com": tmp_path / "https://a.example.com.png"}
