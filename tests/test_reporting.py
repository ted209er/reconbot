from pathlib import Path

from reconbot.models import ReconReport, ReconTarget, ToolResult
from reconbot.reporting import build_markdown_report, write_markdown_report


def test_build_markdown_report_includes_summary_and_output_paths() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )
    report.add_result(ToolResult(name="subfinder", success=True, output="a.example.com\n"))
    report.add_result(ToolResult(name="httpx", success=True, output="https://a.example.com\n"))
    report.add_result(
        ToolResult(
            name="gau",
            success=True,
            output="https://a.example.com/login\nhttps://a.example.com/archive\n",
        )
    )

    markdown = build_markdown_report(
        report,
        {
            "subdomains": Path("data/processed/subdomains.txt"),
            "live_hosts": Path("data/processed/live_urls.txt"),
            "historical_urls": Path("data/processed/historical_urls.txt"),
        },
    )

    assert "# Reconbot Report" in markdown
    assert "- Target domain: `example.com`" in markdown
    assert "- Run timestamp: `" in markdown
    assert "- Subdomain count: 1" in markdown
    assert "- Live host count: 1" in markdown
    assert "- URL count: 2" in markdown
    assert "- Subdomains: `data/processed/subdomains.txt`" in markdown


def test_write_markdown_report_writes_file(tmp_path: Path) -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )
    report_path = tmp_path / "reports" / "example.com.md"

    written_path = write_markdown_report(
        report,
        {
            "subdomains": Path("subdomains.txt"),
            "live_hosts": Path("live_urls.txt"),
            "historical_urls": Path("historical_urls.txt"),
        },
        report_path,
    )

    assert written_path == report_path
    assert report_path.read_text(encoding="utf-8").startswith("# Reconbot Report")
