from pathlib import Path

from pytest import MonkeyPatch

from reconbot import screenshots
from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.models import ToolResult
from reconbot.screenshots import ScreenshotDiagnostic, ScreenshotStatus
from reconbot.utils.subprocess_runner import TIMEOUT_RETURN_CODE


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
        (output_dir / "https-admin-example-com-login.png").write_text(
            "screenshot",
            encoding="utf-8",
        )
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


def test_capture_screenshot_records_failure_reason(
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
        return ToolResult(name="gowitness", success=False, error="browser missing", return_code=1)

    monkeypatch.setattr(screenshots, "run_screenshot_capture", fake_run_screenshot_capture)
    diagnostics: list[ScreenshotDiagnostic] = []
    statuses: list[CollectionStatus] = []

    result = screenshots.capture_screenshot(
        "https://example.com",
        output_dir=tmp_path,
        diagnostics=diagnostics,
        collection_statuses=statuses,
    )

    assert result is None
    assert diagnostics == [
        ScreenshotDiagnostic(
            url="https://example.com",
            status=ScreenshotStatus.FAILED,
            screenshot_path=None,
            return_code=1,
            error="browser missing",
        )
    ]
    assert statuses[0].status == CollectionState.FAILED
    assert statuses[0].error_summary == "browser missing"


def test_capture_screenshot_records_timeout(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    def fake_run_screenshot_capture(
        target: str,
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        return ToolResult(name="gowitness", success=False, return_code=TIMEOUT_RETURN_CODE)

    monkeypatch.setattr(screenshots, "run_screenshot_capture", fake_run_screenshot_capture)
    diagnostics: list[ScreenshotDiagnostic] = []

    result = screenshots.capture_screenshot(
        "https://example.com",
        output_dir=tmp_path,
        diagnostics=diagnostics,
    )

    assert result is None
    assert diagnostics[0].status == ScreenshotStatus.TIMED_OUT


def test_capture_screenshot_rejects_missing_artifact(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        screenshots,
        "run_screenshot_capture",
        lambda target, *, output_dir, binary, timeout: ToolResult(
            name="gowitness",
            success=True,
        ),
    )
    diagnostics: list[ScreenshotDiagnostic] = []

    result = screenshots.capture_screenshot(
        "https://example.com",
        output_dir=tmp_path,
        diagnostics=diagnostics,
    )

    assert result is None
    assert diagnostics[0].status == ScreenshotStatus.NO_ARTIFACT
    assert "missing" in diagnostics[0].error


def test_capture_screenshot_rejects_empty_artifact(
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
        (output_dir / "https-example-com.png").touch()
        return ToolResult(name="gowitness", success=True)

    monkeypatch.setattr(screenshots, "run_screenshot_capture", fake_run_screenshot_capture)
    diagnostics: list[ScreenshotDiagnostic] = []

    result = screenshots.capture_screenshot(
        "https://example.com",
        output_dir=tmp_path,
        diagnostics=diagnostics,
    )

    assert result is None
    assert diagnostics[0].status == ScreenshotStatus.NO_ARTIFACT
    assert "empty" in diagnostics[0].error


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
        diagnostics: object = None,
    ) -> Path:
        return output_dir / f"{url}.png"

    monkeypatch.setattr(screenshots, "capture_screenshot", fake_capture_screenshot)

    result = screenshots.capture_screenshots(["https://a.example.com", "  "], output_dir=tmp_path)

    assert result == {"https://a.example.com": tmp_path / "https://a.example.com.png"}
