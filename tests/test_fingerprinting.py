from pytest import MonkeyPatch

from reconbot import fingerprinting
from reconbot.models import ToolResult


def test_fingerprint_url_uses_httpx_technology_detection(monkeypatch: MonkeyPatch) -> None:
    calls: list[tuple[str, str, float]] = []

    def fake_run_fingerprint_probe(
        target: str,
        *,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        calls.append((target, binary, timeout))
        return ToolResult(
            name="httpx",
            success=True,
            output='{"tech":["React","Next.js"],"webserver":"Nginx","cdn_name":"Cloudflare"}\n',
        )

    monkeypatch.setattr(fingerprinting, "run_fingerprint_probe", fake_run_fingerprint_probe)

    result = fingerprinting.fingerprint_url(
        "https://example.com",
        binary="custom-httpx",
        timeout=30,
    )

    assert result == ["Cloudflare", "Next.js", "Nginx", "React"]
    assert calls == [
        ("https://example.com", "custom-httpx", 30),
    ]


def test_fingerprint_url_returns_empty_list_on_failed_command(
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_run_fingerprint_probe(
        target: str,
        *,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        return ToolResult(name="httpx", success=False, return_code=1)

    monkeypatch.setattr(fingerprinting, "run_fingerprint_probe", fake_run_fingerprint_probe)

    assert fingerprinting.fingerprint_url("https://example.com") == []


def test_fingerprint_urls_skips_blank_targets(monkeypatch: MonkeyPatch) -> None:
    def fake_fingerprint_url_metadata(
        url: str,
        *,
        binary: str,
        timeout: float,
    ) -> fingerprinting.PassiveAssetMetadata:
        return fingerprinting.PassiveAssetMetadata(technologies=[f"tech-for-{url}"])

    monkeypatch.setattr(fingerprinting, "fingerprint_url_metadata", fake_fingerprint_url_metadata)

    result = fingerprinting.fingerprint_urls(["https://a.example.com", "  "])

    assert result == {"https://a.example.com": ["tech-for-https://a.example.com"]}


def test_fingerprint_url_metadata_extracts_passive_metadata(monkeypatch: MonkeyPatch) -> None:
    def fake_run_fingerprint_probe(
        target: str,
        *,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        return ToolResult(
            name="httpx",
            success=True,
            output=(
                '{"tech":["React"],"title":"API Docs","header":{"server":"cloudflare"},'
                '"cdn_name":"Cloudflare","cname":["example.pages.dev"]}\n'
            ),
        )

    monkeypatch.setattr(fingerprinting, "run_fingerprint_probe", fake_run_fingerprint_probe)

    metadata = fingerprinting.fingerprint_url_metadata("https://example.com")

    assert metadata.technologies == ["Cloudflare", "React"]
    assert metadata.response_headers == {"server": "cloudflare"}
    assert metadata.title == "API Docs"
    assert metadata.platform_indicators == ["Cloudflare", "example.pages.dev"]


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
    def fake_run_fingerprint_probe(
        target: str,
        *,
        binary: str,
        timeout: float,
    ) -> ToolResult:
        return ToolResult(
            name="httpx",
            success=True,
            output='not json\n{"technologies":["Django"],"language":"Python"}\n',
        )

    monkeypatch.setattr(fingerprinting, "run_fingerprint_probe", fake_run_fingerprint_probe)

    assert fingerprinting.fingerprint_url("https://example.com") == ["Django", "Python"]
