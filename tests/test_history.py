import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from reconbot.collection_status import CollectionState, CollectionStatus
from reconbot.history import (
    calculate_added_items,
    calculate_added_screenshots,
    calculate_added_technologies,
    calculate_removed_items,
    calculate_removed_screenshots,
    calculate_removed_technologies,
    get_collection_statuses,
    get_historical_url_intelligence,
    get_previous_live_urls,
    get_previous_screenshots,
    get_previous_subdomains,
    get_previous_technologies,
    get_screenshot_diagnostics,
    initialize_database,
    list_recent_runs,
    record_collection_statuses,
    record_historical_url_intelligence,
    record_live_urls,
    record_run,
    record_screenshot_diagnostics,
    record_screenshots,
    record_subdomains,
    record_technologies,
)
from reconbot.screenshots import ScreenshotDiagnostic, ScreenshotStatus
from reconbot.url_intelligence import classify_historical_urls


def test_initialize_database_creates_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "history" / "reconbot.db"

    initialized_path = initialize_database(database_path)

    assert initialized_path == database_path
    assert database_path.exists()


def test_record_run_and_list_recent_runs(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    completed_at = started_at + timedelta(seconds=5)

    run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=completed_at,
        subdomain_count=2,
        live_url_count=1,
        url_count=3,
        database_path=database_path,
    )

    runs = list_recent_runs(database_path=database_path)

    assert run_id == 1
    assert len(runs) == 1
    assert runs[0].target == "example.com"
    assert runs[0].run_name == ""
    assert runs[0].profile == "standard"
    assert runs[0].run_status == "COMPLETE"
    assert runs[0].started_at == started_at.isoformat()
    assert runs[0].completed_at == completed_at.isoformat()
    assert runs[0].subdomain_count == 2
    assert runs[0].live_url_count == 1
    assert runs[0].url_count == 3


def test_list_recent_runs_returns_newest_first_and_respects_limit(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)

    for index in range(3):
        record_run(
            target=f"example{index}.com",
            started_at=started_at + timedelta(minutes=index),
            completed_at=started_at + timedelta(minutes=index, seconds=10),
            subdomain_count=index,
            live_url_count=index,
            url_count=index,
            database_path=database_path,
        )

    runs = list_recent_runs(limit=2, database_path=database_path)

    assert [run.target for run in runs] == ["example2.com", "example1.com"]


def test_record_run_stores_run_name(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)

    record_run(
        target="example.com",
        run_name="daily",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=0,
        url_count=0,
        database_path=database_path,
    )

    runs = list_recent_runs(database_path=database_path)

    assert runs[0].run_name == "daily"


def test_record_run_stores_profile(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)

    record_run(
        target="example.com",
        profile="deep",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=0,
        url_count=0,
        database_path=database_path,
    )

    assert list_recent_runs(database_path=database_path)[0].profile == "deep"


def test_records_and_reads_previous_items_for_latest_target_run(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)

    first_run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=2,
        live_url_count=1,
        url_count=0,
        database_path=database_path,
    )
    record_subdomains(
        run_id=first_run_id,
        subdomains=["b.example.com", "a.example.com", "a.example.com"],
        database_path=database_path,
    )
    record_live_urls(
        run_id=first_run_id,
        urls=["https://b.example.com", "https://a.example.com", "https://a.example.com"],
        database_path=database_path,
    )

    assert get_previous_subdomains(target="example.com", database_path=database_path) == [
        "a.example.com",
        "b.example.com",
    ]
    assert get_previous_live_urls(target="example.com", database_path=database_path) == [
        "https://a.example.com",
        "https://b.example.com",
    ]


def test_previous_items_are_empty_without_matching_target(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"

    assert get_previous_subdomains(target="example.com", database_path=database_path) == []
    assert get_previous_live_urls(target="example.com", database_path=database_path) == []


def test_calculate_added_and_removed_items_are_sorted_and_deduplicated() -> None:
    current = ["beta.example.com", "api.example.com", "api.example.com"]
    previous = ["old.example.com", "api.example.com"]

    assert calculate_added_items(current, previous) == ["beta.example.com"]
    assert calculate_removed_items(current, previous) == ["old.example.com"]


def test_records_and_reads_previous_technologies(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=2,
        url_count=0,
        database_path=database_path,
    )

    record_technologies(
        run_id=run_id,
        technologies={
            "https://a.example.com": ["Nginx", "React", "React"],
            "https://b.example.com": ["Cloudflare"],
        },
        database_path=database_path,
    )

    assert get_previous_technologies(target="example.com", database_path=database_path) == [
        "Cloudflare",
        "Nginx",
        "React",
    ]


def test_calculate_added_and_removed_technologies_are_sorted() -> None:
    current = ["FastAPI", "Nginx", "Nginx"]
    previous = ["Drupal", "Nginx"]

    assert calculate_added_technologies(current, previous) == ["FastAPI"]
    assert calculate_removed_technologies(current, previous) == ["Drupal"]


def test_records_and_reads_previous_screenshots(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=1,
        url_count=0,
        database_path=database_path,
    )

    record_screenshots(
        run_id=run_id,
        screenshots={
            "https://a.example.com": Path("reports/screenshots/example-com/a.png"),
            "https://b.example.com": Path("reports/screenshots/example-com/b.png"),
        },
        captured_at=started_at + timedelta(seconds=5),
        database_path=database_path,
    )

    assert get_previous_screenshots(target="example.com", database_path=database_path) == {
        "https://a.example.com": Path("reports/screenshots/example-com/a.png"),
        "https://b.example.com": Path("reports/screenshots/example-com/b.png"),
    }
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute("SELECT DISTINCT captured_at FROM screenshots").fetchall()
    assert rows == [((started_at + timedelta(seconds=5)).isoformat(),)]


def test_calculate_added_and_removed_screenshots_use_urls() -> None:
    current = {
        "https://admin.example.com": Path("reports/screenshots/example-com/admin.png"),
        "https://blog.example.com": Path("reports/screenshots/example-com/blog.png"),
    }
    previous = {
        "https://blog.example.com": Path("reports/screenshots/example-com/blog-old.png"),
        "https://old.example.com": Path("reports/screenshots/example-com/old.png"),
    }

    assert calculate_added_screenshots(current, previous) == ["https://admin.example.com"]
    assert calculate_removed_screenshots(current, previous) == ["https://old.example.com"]


def test_records_and_reads_collection_statuses(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    run_id = record_run(
        target="example.com",
        run_status="PARTIAL",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=0,
        url_count=0,
        database_path=database_path,
    )
    statuses = [
        CollectionStatus("subfinder", "example.com", CollectionState.SUCCESS, 3, 0),
        CollectionStatus("gau", "example.com", CollectionState.FAILED, 0, 2, "failed"),
    ]

    record_collection_statuses(
        run_id=run_id,
        statuses=statuses,
        database_path=database_path,
    )

    assert list_recent_runs(database_path=database_path)[0].run_status == "PARTIAL"
    assert get_collection_statuses(run_id=run_id, database_path=database_path) == [
        statuses[1],
        statuses[0],
    ]


def test_records_and_reads_screenshot_diagnostics(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=1,
        url_count=0,
        database_path=database_path,
    )
    diagnostics = [
        ScreenshotDiagnostic(
            url="https://example.com",
            status=ScreenshotStatus.NO_ARTIFACT,
            screenshot_path=None,
            return_code=0,
            error="missing artifact",
        )
    ]

    record_screenshot_diagnostics(
        run_id=run_id,
        diagnostics=diagnostics,
        database_path=database_path,
    )

    assert get_screenshot_diagnostics(run_id=run_id, database_path=database_path) == diagnostics


def test_records_and_reads_historical_url_intelligence(tmp_path: Path) -> None:
    database_path = tmp_path / "reconbot.db"
    started_at = datetime(2026, 5, 29, 12, 0, tzinfo=UTC)
    run_id = record_run(
        target="example.com",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5),
        subdomain_count=0,
        live_url_count=0,
        url_count=1,
        database_path=database_path,
    )
    findings = classify_historical_urls(
        {"gau": ["https://example.com/login"], "waybackurls": ["https://example.com/login"]}
    )

    record_historical_url_intelligence(
        run_id=run_id,
        findings=findings,
        database_path=database_path,
    )

    assert get_historical_url_intelligence(
        run_id=run_id,
        database_path=database_path,
    ) == findings
