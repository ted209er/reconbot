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
    assert "- Run name: `default`" in markdown
    assert "- Execution timestamp: `" in markdown
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


def test_build_markdown_report_includes_diff_summary() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )

    markdown = build_markdown_report(
        report,
        {
            "subdomains": Path("subdomains.txt"),
            "live_hosts": Path("live_urls.txt"),
            "historical_urls": Path("historical_urls.txt"),
        },
        {
            "added_subdomains": ["api-v2.example.com", "beta.example.com"],
            "removed_subdomains": ["old-admin.example.com"],
            "added_live_urls": ["https://api-v2.example.com"],
            "removed_live_urls": [],
        },
    )

    assert "## Changes Since Previous Run" in markdown
    assert "- Added subdomains: 2" in markdown
    assert "- Removed subdomains: 1" in markdown
    assert "- Added live URLs: 1" in markdown
    assert "- Removed live URLs: 0" in markdown
    assert "+ api-v2.example.com" in markdown
    assert "+ beta.example.com" in markdown
    assert "- old-admin.example.com" in markdown
    assert "+ https://api-v2.example.com" in markdown


def test_build_markdown_report_includes_technology_summary_and_changes() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )

    markdown = build_markdown_report(
        report,
        {
            "subdomains": Path("subdomains.txt"),
            "live_hosts": Path("live_urls.txt"),
            "historical_urls": Path("historical_urls.txt"),
            "technologies": Path("technologies.txt"),
        },
        technology_summary={"Cloudflare": 12, "Nginx": 8, "WordPress": 3},
        technology_diff={
            "added_technologies": ["FastAPI", "Keycloak"],
            "removed_technologies": ["Drupal"],
        },
    )

    assert "## Technology Summary" in markdown
    assert "- Cloudflare (12)" in markdown
    assert "- Nginx (8)" in markdown
    assert "- WordPress (3)" in markdown
    assert "Technology Changes:" in markdown
    assert "- Added technologies: 2" in markdown
    assert "- Removed technologies: 1" in markdown
    assert "+ FastAPI" in markdown
    assert "+ Keycloak" in markdown
    assert "- Drupal" in markdown
    assert "- Technologies: `technologies.txt`" in markdown


def test_build_markdown_report_includes_run_name() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )

    markdown = build_markdown_report(
        report,
        {
            "subdomains": Path("subdomains.txt"),
            "live_hosts": Path("live_urls.txt"),
            "historical_urls": Path("historical_urls.txt"),
        },
        run_name="daily",
    )

    assert "- Run name: `daily`" in markdown


def test_build_markdown_report_includes_screenshot_summary() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )

    markdown = build_markdown_report(
        report,
        {
            "subdomains": Path("subdomains.txt"),
            "live_hosts": Path("live_urls.txt"),
            "historical_urls": Path("historical_urls.txt"),
            "screenshots": Path("reports/screenshots/example-com"),
        },
        screenshots={
            "https://admin.example.com": Path("reports/screenshots/example-com/admin.png"),
            "https://blog.example.com": Path("reports/screenshots/example-com/blog.png"),
        },
    )

    assert "## Screenshots" in markdown
    assert "- Screenshots Captured: 2" in markdown
    assert "- reports/screenshots/example-com/admin.png" in markdown
    assert "- reports/screenshots/example-com/blog.png" in markdown
    assert "- Screenshots: `reports/screenshots/example-com`" in markdown
