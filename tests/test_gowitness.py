from collections.abc import Sequence
from pathlib import Path

from pytest import MonkeyPatch

from reconbot.models import ToolResult
from reconbot.tools import gowitness


def test_run_screenshot_capture_calls_gowitness(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, list[str], float | None]] = []

    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        calls.append((name, list(command), timeout))
        return ToolResult(name=name, success=True, command=list(command))

    monkeypatch.setattr(gowitness, "run_command", fake_run_command)

    gowitness.run_screenshot_capture(
        "https://admin.example.com/login",
        output_dir=tmp_path,
        binary="custom-gowitness",
        timeout=30,
    )

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


def test_run_basic_check_calls_gowitness_version(monkeypatch: MonkeyPatch) -> None:
    calls: list[tuple[str, list[str], float | None]] = []

    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        calls.append((name, list(command), timeout))
        return ToolResult(name=name, success=True, command=list(command))

    monkeypatch.setattr(gowitness, "run_command", fake_run_command)

    gowitness.run_basic_check(binary="custom-gowitness", timeout=4)

    assert calls == [("gowitness", ["custom-gowitness", "version"], 4)]
