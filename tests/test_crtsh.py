from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot.models import ToolResult
from reconbot.tools import crtsh


def test_parse_crtsh_subdomains_normalizes_and_deduplicates_wildcards() -> None:
    output = """
    [
      {"name_value": "*.b.example.com\\na.example.com", "common_name": "b.example.com"},
      {"name_value": "example.com", "common_name": "*.c.example.com"}
    ]
    """

    result = crtsh.parse_crtsh_subdomains(output, "example.com")

    assert result == ["a.example.com", "b.example.com", "c.example.com"]


def test_find_subdomains_calls_crtsh_with_curl(monkeypatch: MonkeyPatch) -> None:
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
            output='[{"name_value":"a.example.com"}]',
        )

    monkeypatch.setattr(crtsh, "run_command", fake_run_command)

    result = crtsh.find_subdomains("example.com", binary="curl", timeout=30)

    assert result == ["a.example.com"]
    assert calls == [
        ("crtsh", ["curl", "-fsSL", "https://crt.sh/?q=%25.example.com&output=json"], 30)
    ]


def test_parse_crtsh_subdomains_returns_empty_list_for_invalid_json() -> None:
    assert crtsh.parse_crtsh_subdomains("not json", "example.com") == []
