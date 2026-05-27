from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot.models import ToolResult
from reconbot.tools import httpx


def test_find_live_urls_calls_httpx_for_each_subdomain(monkeypatch: MonkeyPatch) -> None:
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
            output=f"https://{command[-1]}\n",
        )

    monkeypatch.setattr(httpx, "run_command", fake_run_command)

    result = httpx.find_live_urls(["a.example.com", "b.example.com"], timeout=30)

    assert result == ["https://a.example.com", "https://b.example.com"]
    assert calls == [
        ("httpx", ["httpx", "-silent", "-u", "a.example.com"], 30),
        ("httpx", ["httpx", "-silent", "-u", "b.example.com"], 30),
    ]


def test_parse_live_urls_filters_and_deduplicates() -> None:
    output = """
    https://b.example.com
    http://a.example.com/
    https://b.example.com/
    not-a-url
    ftp://example.com
    """

    result = httpx.parse_live_urls(output)

    assert result == ["http://a.example.com", "https://b.example.com"]


def test_find_live_urls_skips_failed_results(monkeypatch: MonkeyPatch) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        if command[-1] == "bad.example.com":
            return ToolResult(
                name=name,
                success=False,
                command=list(command),
                error="failed",
                return_code=1,
            )
        return ToolResult(
            name=name,
            success=True,
            command=list(command),
            output="https://good.example.com\n",
        )

    monkeypatch.setattr(httpx, "run_command", fake_run_command)

    result = httpx.find_live_urls(["bad.example.com", "good.example.com"])

    assert result == ["https://good.example.com"]
