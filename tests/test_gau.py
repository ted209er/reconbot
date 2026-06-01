from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.models import ToolResult
from reconbot.tools import gau


def test_find_urls_calls_gau_with_domain(monkeypatch: MonkeyPatch) -> None:
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
            output="https://example.com/a\nhttps://example.com/b\n",
        )

    monkeypatch.setattr(gau, "run_command", fake_run_command)

    statuses: list[CollectionStatus] = []
    result = gau.find_urls("example.com", timeout=30, collection_statuses=statuses)

    assert result == ["https://example.com/a", "https://example.com/b"]
    assert calls == [("gau", ["gau", "example.com"], 30)]
    assert statuses[0].status == CollectionState.SUCCESS


def test_find_urls_accepts_live_host_list(monkeypatch: MonkeyPatch) -> None:
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

    monkeypatch.setattr(gau, "run_command", fake_run_command)

    result = gau.find_urls(["a.example.com", " ", "b.example.com"], timeout=30)

    assert result == ["https://a.example.com/path", "https://b.example.com/path"]
    assert calls == [
        ("gau", ["gau", "a.example.com"], 30),
        ("gau", ["gau", "b.example.com"], 30),
    ]


def test_parse_urls_filters_deduplicates_and_sorts() -> None:
    output = """
    https://example.com/b
    http://example.com/a
    https://example.com/b
    ftp://example.com/file
    not-a-url
    """

    result = gau.parse_urls(output)

    assert result == ["http://example.com/a", "https://example.com/b"]


def test_find_urls_returns_empty_list_on_failure(monkeypatch: MonkeyPatch) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        return ToolResult(
            name=name,
            success=False,
            command=list(command),
            error="failed",
            return_code=1,
        )

    monkeypatch.setattr(gau, "run_command", fake_run_command)

    assert gau.find_urls("example.com") == []
