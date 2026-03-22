"""
Database - SQLite persistence for job applications
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from .models import Application, ApplicationStatus, Job, Resume


class Database:
    """
    Lightweight SQLite wrapper for persisting job applications.
    """

    def __init__(self, db_path: str = "applications.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url     TEXT UNIQUE,
                    job_title   TEXT,
                    company     TEXT,
                    location    TEXT,
                    source      TEXT,
                    match_score INTEGER,
                    status      TEXT,
                    applied_at  TEXT,
                    error       TEXT,
                    cover_letter TEXT,
                    notes       TEXT,
                    screenshot  TEXT,
                    confirmation TEXT,
                    job_data    TEXT,
                    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save_application(self, app: Application):
        """Insert or update an application record."""
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO applications
                    (job_url, job_title, company, location, source, match_score,
                     status, applied_at, error, cover_letter, notes, screenshot,
                     confirmation, job_data)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(job_url) DO UPDATE SET
                    status=excluded.status,
                    applied_at=excluded.applied_at,
                    error=excluded.error,
                    cover_letter=excluded.cover_letter,
                    notes=excluded.notes,
                    screenshot=excluded.screenshot,
                    confirmation=excluded.confirmation
            """, (
                app.job.url if app.job else "",
                app.job.title if app.job else "",
                app.job.company if app.job else "",
                app.job.location if app.job else "",
                app.job.source if app.job else "",
                app.job.match_score if app.job else 0,
                app.status.value,
                app.applied_at,
                app.error,
                app.cover_letter,
                app.notes,
                app.screenshot_path,
                app.confirmation_text,
                json.dumps(app.job.__dict__ if app.job else {}),
            ))

    def get_application(self, job_url: str) -> Optional[dict]:
        """Return application record for a URL, or None if not found."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE job_url=?", (job_url,)
            ).fetchone()
            if row:
                cols = [d[0] for d in conn.execute("SELECT * FROM applications LIMIT 0").description]
                return dict(zip(cols, row))
        return None

    def get_all_applications(self) -> list[dict]:
        """Return all applications ordered by date."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY created_at DESC"
            ).fetchall()
            if not rows:
                return []
            cols = [d[0] for d in conn.execute("SELECT * FROM applications LIMIT 0").description]
            return [dict(zip(cols, row)) for row in rows]

    def update_status(self, job_url: str, status: str, notes: str = ""):
        """Manually update application status."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE applications SET status=?, notes=? WHERE job_url=?",
                (status, notes, job_url)
            )

    def get_stats(self) -> dict:
        """Return summary statistics."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM applications GROUP BY status"
            ).fetchall()
        stats = {row[0]: row[1] for row in rows}
        stats["total"] = sum(stats.values())
        return stats
