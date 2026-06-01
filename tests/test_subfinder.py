from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.models import ToolResult
from reconbot.tools import subfinder


def test_find_subdomains_calls_subfinder_with_domain(monkeypatch: MonkeyPatch) -> None:
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
            output="b.example.com\na.example.com\n",
        )

    monkeypatch.setattr(subfinder, "run_command", fake_run_command)

    statuses: list[CollectionStatus] = []
    result = subfinder.find_subdomains("example.com", timeout=30, collection_statuses=statuses)

    assert result == ["a.example.com", "b.example.com"]
    assert calls == [("subfinder", ["subfinder", "-silent", "-d", "example.com"], 30)]
    assert statuses[0].status == CollectionState.SUCCESS


def test_parse_subdomains_deduplicates_sorts_and_filters() -> None:
    output = """
    B.EXAMPLE.COM
    a.example.com
    b.example.com.
    example.com
    other.test
    """

    result = subfinder.parse_subdomains(output, "example.com")

    assert result == ["a.example.com", "b.example.com"]


def test_find_subdomains_returns_empty_list_on_failure(monkeypatch: MonkeyPatch) -> None:
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
            error="missing executable",
            return_code=127,
        )

    monkeypatch.setattr(subfinder, "run_command", fake_run_command)

    assert subfinder.find_subdomains("example.com") == []
