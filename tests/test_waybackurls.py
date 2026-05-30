from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot.models import ToolResult
from reconbot.tools import waybackurls


def test_find_urls_calls_waybackurls_for_each_target(monkeypatch: MonkeyPatch) -> None:
    calls: list[tuple[str, list[str], float | None]] = []

    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        calls.append((name, list(command), timeout))
        return ToolResult(
            name=name,
            success=True,
            command=list(command),
            output=f"https://{command[-1]}/path\n",
        )

    monkeypatch.setattr(waybackurls, "run_command", fake_run_command)

    result = waybackurls.find_urls(["a.example.com", " ", "b.example.com"], timeout=30)

    assert result == ["https://a.example.com/path", "https://b.example.com/path"]
    assert calls == [
        ("waybackurls", ["waybackurls", "a.example.com"], 30),
        ("waybackurls", ["waybackurls", "b.example.com"], 30),
    ]


def test_find_urls_skips_failed_results(monkeypatch: MonkeyPatch) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        return ToolResult(name=name, success=False, command=list(command), return_code=1)

    monkeypatch.setattr(waybackurls, "run_command", fake_run_command)

    assert waybackurls.find_urls("example.com") == []
