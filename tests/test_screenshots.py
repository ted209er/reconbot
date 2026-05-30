from collections.abc import Sequence
from pathlib import Path

from pytest import MonkeyPatch

from reconbot import screenshots
from reconbot.models import ToolResult


def test_capture_screenshot_calls_gowitness(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, list[str], float | None]] = []

    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        calls.append((name, list(command), timeout))
        return ToolResult(name=name, success=True, command=list(command))

    monkeypatch.setattr(screenshots, "run_command", fake_run_command)

    result = screenshots.capture_screenshot(
        "https://admin.example.com/login",
        output_dir=tmp_path,
        binary="custom-gowitness",
        timeout=30,
    )

    assert result == tmp_path / "https-admin.example.com-login.png"
    assert calls == [
        (
            "gowitness",
            [
                "custom-gowitness",
                "scan",
                "single",
                "--url",
                "https://admin.example.com/login",
                "--screenshot-path",
                str(tmp_path),
            ],
            30,
        )
    ]


def test_capture_screenshot_returns_none_on_failure(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        return ToolResult(name=name, success=False, command=list(command), return_code=1)

    monkeypatch.setattr(screenshots, "run_command", fake_run_command)

    assert screenshots.capture_screenshot("https://example.com", output_dir=tmp_path) is None


def test_capture_screenshots_skips_blank_urls(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    def fake_capture_screenshot(
        url: str,
        *,
        output_dir: Path,
        binary: str,
        timeout: float,
    ) -> Path:
        return output_dir / f"{url}.png"

    monkeypatch.setattr(screenshots, "capture_screenshot", fake_capture_screenshot)

    result = screenshots.capture_screenshots(["https://a.example.com", "  "], output_dir=tmp_path)

    assert result == {"https://a.example.com": tmp_path / "https://a.example.com.png"}
