from datetime import UTC, datetime, timedelta
from pathlib import Path

from reconbot.history import (
    calculate_added_items,
    calculate_added_technologies,
    calculate_removed_items,
    calculate_removed_technologies,
    get_previous_live_urls,
    get_previous_screenshots,
    get_previous_subdomains,
    get_previous_technologies,
    initialize_database,
    list_recent_runs,
    record_live_urls,
    record_run,
    record_screenshots,
    record_subdomains,
    record_technologies,
)


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
        database_path=database_path,
    )

    assert get_previous_screenshots(target="example.com", database_path=database_path) == [
        "reports/screenshots/example-com/a.png",
        "reports/screenshots/example-com/b.png",
    ]
