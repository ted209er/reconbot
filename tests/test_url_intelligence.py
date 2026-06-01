from pathlib import Path

from reconbot.models import ReconReport, ReconTarget
from reconbot.reporting import build_markdown_report
from reconbot.url_intelligence import (
    HistoricalUrlConfidence,
    classify_historical_url,
    classify_historical_urls,
    summarize_historical_urls,
    top_historical_leads,
    write_historical_url_tsv,
)


def test_classifies_multiple_categories_and_query_keys() -> None:
    finding = classify_historical_url(
        "https://example.com/wp-login.php?redirect_to=/admin&user=test",
        sources=["waybackurls", "gau"],
    )

    assert finding.hostname == "example.com"
    assert finding.path == "/wp-login.php"
    assert finding.query_keys == ("redirect_to", "user")
    assert finding.categories == ("Authentication", "CMS", "Redirect Candidate")
    assert finding.sources == ("gau", "waybackurls")
    assert finding.confidence == HistoricalUrlConfidence.HIGH
    assert finding.reasons == (
        "Authentication: keyword: login",
        "CMS: keyword: wp-login",
        "Redirect Candidate: query key: redirect_to",
    )


def test_classifies_suffixes_and_redirect_candidates() -> None:
    source_map = classify_historical_url("https://static.example.com/app.js.map")
    redirect = classify_historical_url("https://example.com/out?url=https://example.net")

    assert source_map.categories == ("Source Map",)
    assert source_map.confidence == HistoricalUrlConfidence.HIGH
    assert redirect.categories == ("Redirect Candidate",)
    assert redirect.reasons == ("Redirect Candidate: query key: url",)


def test_keyword_rules_do_not_match_broad_substrings() -> None:
    finding = classify_historical_url("https://example.com/capital")

    assert finding.categories == ("Unknown",)


def test_classify_historical_urls_preserves_provenance_and_summary() -> None:
    findings = classify_historical_urls(
        {
            "gau": ["https://example.com/login", "https://example.com/api/users"],
            "waybackurls": ["https://example.com/login"],
        }
    )

    assert [finding.url for finding in findings] == [
        "https://example.com/api/users",
        "https://example.com/login",
    ]
    assert findings[1].sources == ("gau", "waybackurls")
    assert summarize_historical_urls(findings) == {"Authentication": 1, "API": 1}


def test_top_historical_leads_prioritizes_signal_and_limits_output() -> None:
    findings = [
        classify_historical_url(f"https://example.com/static/{index}.css")
        for index in range(30)
    ]
    findings.append(classify_historical_url("https://example.com/settings.yml"))

    leads = top_historical_leads(findings)

    assert len(leads) == 25
    assert leads[0].url == "https://example.com/settings.yml"


def test_write_historical_url_tsv_is_human_readable(tmp_path: Path) -> None:
    output_path = tmp_path / "data" / "processed" / "historical-urls-classified.tsv"
    findings = classify_historical_urls({"gau": ["https://example.com/login?next=/account"]})

    written_path = write_historical_url_tsv(findings, output_path)

    assert written_path == output_path
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == (
        "url\tobservation_type\treachability\thostname\tpath\tquery_keys\tcategories\t"
        "sources\tconfidence\treasons"
    )
    assert lines[1].startswith(
        "https://example.com/login?next=/account\tHistorical Lead\tunverified\t"
        "example.com\t/login\tnext\t"
    )


def test_markdown_distinguishes_historical_leads_from_current_observations() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )
    findings = classify_historical_urls({"gau": ["https://example.com/login"]})

    markdown = build_markdown_report(
        report,
        {
            "subdomains": Path("subdomains.txt"),
            "live_hosts": Path("live_urls.txt"),
            "historical_urls": Path("historical_urls.txt"),
        },
        historical_url_intelligence=findings,
        historical_url_summary=summarize_historical_urls(findings),
    )

    assert "## Historical URL Intelligence" in markdown
    assert "- Classification: Historical Lead" in markdown
    assert "- Reachability: unverified" in markdown
    assert "not current observations" in markdown
    assert "evidence that an archived URL remains reachable" in markdown
    assert "- Authentication: 1" in markdown
