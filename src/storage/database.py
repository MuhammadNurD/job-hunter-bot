from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.jobs.allan_gray import JobListing


class JobDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    closing_date TEXT,
                    description TEXT,
                    apply_url TEXT,
                    source TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    alerted INTEGER DEFAULT 0
                )
                """
            )

    def upsert_job(self, job: JobListing) -> bool:
        job_id = job.stable_id()
        with self._connect() as conn:
            row = conn.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            now = job.discovered_at
            if row:
                conn.execute(
                    """
                    UPDATE jobs
                    SET title = ?, company = ?, location = ?, closing_date = ?,
                        description = ?, apply_url = ?, source = ?, last_seen = ?
                    WHERE job_id = ?
                    """,
                    (
                        job.title,
                        job.company,
                        job.location,
                        job.closing_date,
                        job.description,
                        job.apply_url,
                        job.source,
                        now,
                        job_id,
                    ),
                )
                return False

            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, title, company, location, closing_date, description,
                    apply_url, source, first_seen, last_seen, alerted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    job_id,
                    job.title,
                    job.company,
                    job.location,
                    job.closing_date,
                    job.description,
                    job.apply_url,
                    job.source,
                    now,
                    now,
                ),
            )
            return True

    def mark_alerted(self, job_id: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE jobs SET alerted = 1 WHERE job_id = ?", (job_id,))

    def list_jobs(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY last_seen DESC").fetchall()
            return [dict(row) for row in rows]

    def job_to_listing(self, row: dict) -> JobListing:
        return JobListing(
            title=row["title"],
            company=row["company"],
            location=row.get("location") or "",
            closing_date=row.get("closing_date") or "",
            description=row.get("description") or "",
            apply_url=row.get("apply_url") or "",
            source=row.get("source") or "",
            job_id=row["job_id"],
            discovered_at=row.get("last_seen") or "",
        )

    def export_json(self, output: Path) -> None:
        output.write_text(json.dumps(self.list_jobs(), indent=2), encoding="utf-8")
