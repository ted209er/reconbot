"""Lightweight SQLite run history helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_DATABASE_PATH = Path("data/reconbot.db")


@dataclass(frozen=True, slots=True)
class RunHistoryEntry:
    """One recorded Reconbot run."""

    id: int
    target: str
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
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                subdomain_count INTEGER NOT NULL,
                live_url_count INTEGER NOT NULL,
                url_count INTEGER NOT NULL
            )
            """
        )
    return database_path


def record_run(
    *,
    target: str,
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
                started_at,
                completed_at,
                subdomain_count,
                live_url_count,
                url_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                target,
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
            started_at=str(row[2]),
            completed_at=str(row[3]),
            subdomain_count=int(row[4]),
            live_url_count=int(row[5]),
            url_count=int(row[6]),
        )
        for row in rows
    ]
