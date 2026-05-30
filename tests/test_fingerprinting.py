from collections.abc import Sequence

from pytest import MonkeyPatch

from reconbot import fingerprinting
from reconbot.models import ToolResult


def test_fingerprint_url_uses_httpx_technology_detection(monkeypatch: MonkeyPatch) -> None:
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
            output='{"tech":["React","Next.js"],"webserver":"Nginx","cdn_name":"Cloudflare"}\n',
        )

    monkeypatch.setattr(fingerprinting, "run_command", fake_run_command)

    result = fingerprinting.fingerprint_url(
        "https://example.com",
        binary="custom-httpx",
        timeout=30,
    )

    assert result == ["Cloudflare", "Next.js", "Nginx", "React"]
    assert calls == [
        (
            "httpx",
            ["custom-httpx", "-silent", "-json", "-tech-detect", "-u", "https://example.com"],
            30,
        )
    ]


def test_fingerprint_url_returns_empty_list_on_failed_command(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        return ToolResult(name=name, success=False, command=list(command), return_code=1)

    monkeypatch.setattr(fingerprinting, "run_command", fake_run_command)

    assert fingerprinting.fingerprint_url("https://example.com") == []


def test_fingerprint_urls_skips_blank_targets(monkeypatch: MonkeyPatch) -> None:
    def fake_fingerprint_url(url: str, *, binary: str, timeout: float) -> list[str]:
        return [f"tech-for-{url}"]

    monkeypatch.setattr(fingerprinting, "fingerprint_url", fake_fingerprint_url)

    result = fingerprinting.fingerprint_urls(["https://a.example.com", "  "])

    assert result == {"https://a.example.com": ["tech-for-https://a.example.com"]}


def test_summarize_technologies_counts_one_technology_per_url() -> None:
    fingerprints = {
        "https://a.example.com": ["Nginx", "React", "React"],
        "https://b.example.com": ["Nginx", "WordPress"],
    }

    assert fingerprinting.summarize_technologies(fingerprints) == {
        "Nginx": 2,
        "React": 1,
        "WordPress": 1,
    }


def test_fingerprint_url_ignores_invalid_json(monkeypatch: MonkeyPatch) -> None:
    def fake_run_command(
        name: str,
        command: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> ToolResult:
        return ToolResult(
            name=name,
            success=True,
            command=list(command),
            output='not json\n{"technologies":["Django"],"language":"Python"}\n',
        )

    monkeypatch.setattr(fingerprinting, "run_command", fake_run_command)

    assert fingerprinting.fingerprint_url("https://example.com") == ["Django", "Python"]
