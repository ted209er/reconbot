from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.models import ToolResult
from reconbot.tools import assetfinder


def test_find_subdomains_calls_assetfinder(monkeypatch: MonkeyPatch) -> None:
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

    monkeypatch.setattr(assetfinder, "run_command", fake_run_command)

    statuses: list[CollectionStatus] = []
    result = assetfinder.find_subdomains(
        "example.com",
        binary="custom-assetfinder",
        timeout=30,
        collection_statuses=statuses,
    )

    assert result == ["a.example.com", "b.example.com"]
    assert calls == [
        ("assetfinder", ["custom-assetfinder", "--subs-only", "example.com"], 30)
    ]
    assert statuses[0].status == CollectionState.SUCCESS


def test_find_subdomains_returns_empty_list_on_failure(monkeypatch: MonkeyPatch) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        return ToolResult(name=name, success=False, command=list(command), return_code=1)

    monkeypatch.setattr(assetfinder, "run_command", fake_run_command)

    assert assetfinder.find_subdomains("example.com") == []
