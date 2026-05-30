import json
from pathlib import Path

from reconbot.exporting import build_json_export, write_json_export
from reconbot.models import ReconReport, ReconTarget
from reconbot.prioritization import PrioritizedAsset


def test_build_json_export_includes_expected_structure() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )
    report.complete()

    export = build_json_export(
        report=report,
        run_name="daily",
        output_files={
            "subdomains": Path("data/processed/subdomains.txt"),
            "live_hosts": Path("data/processed/live_urls.txt"),
        },
        report_path=Path("reports/example.com.md"),
        subdomains=["b.example.com", "a.example.com"],
        live_urls=["https://b.example.com", "https://a.example.com"],
        historical_urls=["https://example.com/login"],
        technology_summary={"Nginx": 2, "Cloudflare": 1},
        technology_diff={"added_technologies": ["Nginx"], "removed_technologies": []},
        screenshots={
            "https://b.example.com": Path("reports/screenshots/example-com/b.png"),
            "https://a.example.com": Path("reports/screenshots/example-com/a.png"),
        },
        screenshot_diff={
            "added_screenshots": ["https://b.example.com"],
            "removed_screenshots": [],
        },
        prioritized_assets=[
            PrioritizedAsset(
                url="https://a.example.com",
                score=6,
                reasons=["Screenshot available", "New live URL"],
            )
        ],
        subdomain_sources={"subfinder": 2, "assetfinder": 1, "crtsh": 3},
        historical_url_sources={"gau": 1, "waybackurls": 2},
    )

    assert export["target"] == "example.com"
    assert export["run_name"] == "daily"
    assert export["completed_at"] is not None
    assert export["report_path"] == "reports/example.com.md"
    assert export["counts"] == {
        "subdomains": 2,
        "live_urls": 2,
        "historical_urls": 1,
        "technologies": 2,
        "screenshots": 2,
    }
    assert export["subdomains"] == ["a.example.com", "b.example.com"]
    assert export["live_urls"] == ["https://a.example.com", "https://b.example.com"]
    assert export["technology_summary"] == {"Cloudflare": 1, "Nginx": 2}
    assert export["screenshot_paths"] == {
        "https://a.example.com": "reports/screenshots/example-com/a.png",
        "https://b.example.com": "reports/screenshots/example-com/b.png",
    }
    assert export["prioritized_assets"] == [
        {
            "url": "https://a.example.com",
            "score": 6,
            "reasons": ["New live URL", "Screenshot available"],
        }
    ]
    assert export["discovery_sources"] == {
        "subdomains": {"assetfinder": 1, "crtsh": 3, "subfinder": 2},
        "historical_urls": {"gau": 1, "waybackurls": 2},
    }


def test_build_json_export_sorts_change_lists() -> None:
    report = ReconReport(
        target=ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    )

    export = build_json_export(
        report=report,
        run_name="",
        output_files={},
        report_path=Path("reports/example.com.md"),
        subdomains=[],
        live_urls=[],
        historical_urls=[],
        technology_summary={},
        technology_diff={"added_technologies": ["React", "Apache"]},
        screenshots={},
        screenshot_diff={"added_screenshots": ["https://b.example.com", "https://a.example.com"]},
        prioritized_assets=[],
        subdomain_sources={},
        historical_url_sources={},
    )

    assert export["technology_changes"] == {"added_technologies": ["Apache", "React"]}
    assert export["screenshot_changes"] == {
        "added_screenshots": ["https://a.example.com", "https://b.example.com"]
    }


def test_write_json_export_writes_human_readable_json(tmp_path: Path) -> None:
    export_path = tmp_path / "reports" / "json" / "example-com.json"

    written_path = write_json_export({"target": "example.com", "items": ["b", "a"]}, export_path)

    assert written_path == export_path
    content = export_path.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert json.loads(content) == {"target": "example.com", "items": ["b", "a"]}
    assert content.startswith("{\n  ")
