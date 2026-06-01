"""Lightweight SQLite run history helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from reconbot.collection_status import CollectionState, CollectionStatus, RunCompleteness
from reconbot.screenshots import ScreenshotDiagnostic, ScreenshotStatus

DEFAULT_DATABASE_PATH = Path("data/reconbot.db")


@dataclass(frozen=True, slots=True)
class RunHistoryEntry:
    """One recorded Reconbot run."""

    id: int
    target: str
    run_name: str
    profile: str
    run_status: str
    started_at: str
    completed_at: str
    subdomain_count: int
    live_url_count: int
    url_count: int


def initialize_database(database_path: Path = DEFAULT_DATABASE_PATH) -> Path:
    """Create the run history database and schema if needed."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                run_name TEXT NOT NULL DEFAULT '',
                profile TEXT NOT NULL DEFAULT 'standard',
                run_status TEXT NOT NULL DEFAULT 'COMPLETE',
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                subdomain_count INTEGER NOT NULL,
                live_url_count INTEGER NOT NULL,
                url_count INTEGER NOT NULL
            )
            """
        )
        _ensure_column(
            connection,
            table="runs",
            column="run_name",
            definition="TEXT NOT NULL DEFAULT ''",
        )
        _ensure_column(
            connection,
            table="runs",
            column="profile",
            definition="TEXT NOT NULL DEFAULT 'standard'",
        )
        _ensure_column(
            connection,
            table="runs",
            column="run_status",
            definition="TEXT NOT NULL DEFAULT 'COMPLETE'",
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subdomains (
                run_id INTEGER NOT NULL,
                subdomain TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS live_urls (
                run_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS technologies (
                run_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                technology TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS screenshots (
                run_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                screenshot_path TEXT NOT NULL,
                captured_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS collection_statuses (
                run_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                return_code INTEGER,
                error_summary TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS screenshot_diagnostics (
                run_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                screenshot_path TEXT,
                return_code INTEGER NOT NULL,
                error TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
            """
        )
        _ensure_column(
            connection,
            table="screenshots",
            column="captured_at",
            definition="TEXT NOT NULL DEFAULT ''",
        )
    return database_path


def record_run(
    *,
    target: str,
    run_name: str = "",
    profile: str = "standard",
    run_status: str = RunCompleteness.COMPLETE.value,
    started_at: datetime,
    completed_at: datetime,
    subdomain_count: int,
    live_url_count: int,
    url_count: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Record one completed recon run and return its database id."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO runs (
                target,
                run_name,
                profile,
                run_status,
                started_at,
                completed_at,
                subdomain_count,
                live_url_count,
                url_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target,
                run_name,
                profile,
                run_status,
                started_at.isoformat(),
                completed_at.isoformat(),
                subdomain_count,
                live_url_count,
                url_count,
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("failed to record run history")
        return cursor.lastrowid


def list_recent_runs(
    *,
    limit: int = 10,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[RunHistoryEntry]:
    """Return recent recon runs, newest first."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                target,
                run_name,
                profile,
                run_status,
                started_at,
                completed_at,
                subdomain_count,
                live_url_count,
                url_count
            FROM runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        RunHistoryEntry(
            id=int(row[0]),
            target=str(row[1]),
            run_name=str(row[2]),
            profile=str(row[3]),
            run_status=str(row[4]),
            started_at=str(row[5]),
            completed_at=str(row[6]),
            subdomain_count=int(row[7]),
            live_url_count=int(row[8]),
            url_count=int(row[9]),
        )
        for row in rows
    ]


def _ensure_column(
    connection: sqlite3.Connection,
    *,
    table: str,
    column: str,
    definition: str,
) -> None:
    """Add a missing column for lightweight schema evolution."""
    existing_columns = {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing_columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def record_subdomains(
    *,
    run_id: int,
    subdomains: list[str],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Record discovered subdomains for one run."""
    _record_items(
        table="subdomains",
        column="subdomain",
        run_id=run_id,
        values=subdomains,
        database_path=database_path,
    )


def record_live_urls(
    *,
    run_id: int,
    urls: list[str],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Record discovered live URLs for one run."""
    _record_items(
        table="live_urls",
        column="url",
        run_id=run_id,
        values=urls,
        database_path=database_path,
    )


def get_previous_subdomains(
    *,
    target: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[str]:
    """Return subdomains from the most recent previous run for a target."""
    return _get_previous_items(
        target=target,
        table="subdomains",
        column="subdomain",
        database_path=database_path,
    )


def get_previous_live_urls(
    *,
    target: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[str]:
    """Return live URLs from the most recent previous run for a target."""
    return _get_previous_items(
        target=target,
        table="live_urls",
        column="url",
        database_path=database_path,
    )


def record_technologies(
    *,
    run_id: int,
    technologies: dict[str, list[str]],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Record technology fingerprints for one run."""
    initialize_database(database_path)
    rows = [
        (run_id, url, technology)
        for url, values in sorted(technologies.items())
        for technology in sorted(set(values))
    ]
    if not rows:
        return
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            "INSERT INTO technologies (run_id, url, technology) VALUES (?, ?, ?)",
            rows,
        )


def get_previous_technologies(
    *,
    target: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[str]:
    """Return technologies from the most recent previous run for a target."""
    return _get_previous_items(
        target=target,
        table="technologies",
        column="technology",
        database_path=database_path,
    )


def record_screenshots(
    *,
    run_id: int,
    screenshots: dict[str, Path],
    captured_at: datetime | None = None,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Record screenshot paths for one run."""
    initialize_database(database_path)
    captured_at_value = (captured_at or datetime.now(UTC)).isoformat()
    rows = [
        (run_id, url, str(path), captured_at_value)
        for url, path in sorted(screenshots.items())
    ]
    if not rows:
        return
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO screenshots (run_id, url, screenshot_path, captured_at)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )


def record_collection_statuses(
    *,
    run_id: int,
    statuses: list[CollectionStatus],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Record collection quality evidence for one run."""
    initialize_database(database_path)
    rows = [
        (
            run_id,
            status.source,
            status.target,
            status.status.value,
            status.result_count,
            status.return_code,
            status.error_summary,
        )
        for status in sorted(statuses, key=_collection_status_sort_key)
    ]
    if not rows:
        return
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO collection_statuses (
                run_id,
                source,
                target,
                status,
                result_count,
                return_code,
                error_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def get_collection_statuses(
    *,
    run_id: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[CollectionStatus]:
    """Return deterministic collection quality evidence for one run."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT source, target, status, result_count, return_code, error_summary
            FROM collection_statuses
            WHERE run_id = ?
            ORDER BY source, target, status
            """,
            (run_id,),
        ).fetchall()
    return [
        CollectionStatus(
            source=str(row[0]),
            target=str(row[1]),
            status=CollectionState(str(row[2])),
            result_count=int(row[3]),
            return_code=int(row[4]) if row[4] is not None else None,
            error_summary=str(row[5]),
        )
        for row in rows
    ]


def record_screenshot_diagnostics(
    *,
    run_id: int,
    diagnostics: list[ScreenshotDiagnostic],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Record auditable per-URL screenshot collection results."""
    initialize_database(database_path)
    rows = [
        (
            run_id,
            diagnostic.url,
            diagnostic.status.value,
            str(diagnostic.screenshot_path) if diagnostic.screenshot_path is not None else None,
            diagnostic.return_code,
            diagnostic.error,
        )
        for diagnostic in sorted(diagnostics, key=lambda item: item.url)
    ]
    if not rows:
        return
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO screenshot_diagnostics (
                run_id,
                url,
                status,
                screenshot_path,
                return_code,
                error
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def get_screenshot_diagnostics(
    *,
    run_id: int,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> list[ScreenshotDiagnostic]:
    """Return deterministic per-URL screenshot collection results."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT url, status, screenshot_path, return_code, error
            FROM screenshot_diagnostics
            WHERE run_id = ?
            ORDER BY url
            """,
            (run_id,),
        ).fetchall()
    return [
        ScreenshotDiagnostic(
            url=str(row[0]),
            status=ScreenshotStatus(str(row[1])),
            screenshot_path=Path(str(row[2])) if row[2] is not None else None,
            return_code=int(row[3]),
            error=str(row[4]),
        )
        for row in rows
    ]


def get_previous_screenshots(
    *,
    target: str,
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> dict[str, Path]:
    """Return screenshot paths keyed by URL from the most recent previous run."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        run_id = _get_latest_run_id(connection, target)
        if run_id is None:
            return {}
        rows = connection.execute(
            """
            SELECT url, screenshot_path
            FROM screenshots
            WHERE run_id = ?
            ORDER BY url
            """,
            (run_id,),
        ).fetchall()
    return {str(row[0]): Path(str(row[1])) for row in rows}


def calculate_added_items(current: list[str], previous: list[str]) -> list[str]:
    """Return items present now but not in the previous run."""
    return sorted(set(current) - set(previous))


def calculate_removed_items(current: list[str], previous: list[str]) -> list[str]:
    """Return items present in the previous run but missing now."""
    return sorted(set(previous) - set(current))


def calculate_added_technologies(current: list[str], previous: list[str]) -> list[str]:
    """Return technologies present now but not in the previous run."""
    return calculate_added_items(current, previous)


def calculate_removed_technologies(current: list[str], previous: list[str]) -> list[str]:
    """Return technologies present in the previous run but missing now."""
    return calculate_removed_items(current, previous)


def calculate_added_screenshots(
    current: dict[str, Path],
    previous: dict[str, Path],
) -> list[str]:
    """Return screenshot URLs present now but not in the previous run."""
    return calculate_added_items(list(current), list(previous))


def calculate_removed_screenshots(
    current: dict[str, Path],
    previous: dict[str, Path],
) -> list[str]:
    """Return screenshot URLs present in the previous run but missing now."""
    return calculate_removed_items(list(current), list(previous))


def _record_items(
    *,
    table: str,
    column: str,
    run_id: int,
    values: list[str],
    database_path: Path,
) -> None:
    """Record sorted unique values for a run."""
    initialize_database(database_path)
    rows = [(run_id, value) for value in sorted(set(values))]
    if not rows:
        return
    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            f"INSERT INTO {table} (run_id, {column}) VALUES (?, ?)",
            rows,
        )


def _get_previous_items(
    *,
    target: str,
    table: str,
    column: str,
    database_path: Path,
) -> list[str]:
    """Return sorted items for the latest run matching a target."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        run_id = _get_latest_run_id(connection, target)
        if run_id is None:
            return []
        rows = connection.execute(
            f"""
            SELECT {column}
            FROM {table}
            WHERE run_id = ?
            ORDER BY {column}
            """,
            (run_id,),
        ).fetchall()
    return [str(row[0]) for row in rows]


def _get_latest_run_id(connection: sqlite3.Connection, target: str) -> int | None:
    """Return the latest run id for a target."""
    row = connection.execute(
        """
        SELECT id
        FROM runs
        WHERE target = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (target,),
    ).fetchone()
    if row is None:
        return None
    return int(row[0])


def _collection_status_sort_key(status: CollectionStatus) -> tuple[str, str, str]:
    """Return stable ordering for persisted collection evidence."""
    return (status.source, status.target, status.status.value)
