from datetime import UTC, datetime, timedelta
from pathlib import Path

from reconbot.history import initialize_database, list_recent_runs, record_run


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
