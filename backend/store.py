"""SQLite persistence shared by the HTTP services and CLI."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "releaseproof.sqlite3"


class Store:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("RELEASEPROOF_DB", str(DEFAULT_DB)))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT, version INTEGER, payload TEXT NOT NULL,
                    PRIMARY KEY (id, version));
                CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, analysis_id TEXT,
                    status TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE UNIQUE INDEX IF NOT EXISTS active_job ON jobs(analysis_id)
                    WHERE status IN ('queued', 'running');
            """)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def get(self, analysis_id, version=None):
        with self.connect() as db:
            row = db.execute(
                "SELECT payload FROM analyses WHERE id=? " +
                ("AND version=?" if version is not None else "ORDER BY version DESC LIMIT 1"),
                (analysis_id, version) if version is not None else (analysis_id,),
            ).fetchone()
        if row is None:
            raise KeyError("Analysis not found")
        return json.loads(row[0])

    def save(self, analysis, expected_version=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT MAX(version) FROM analyses WHERE id=?", (analysis["id"],)).fetchone()[0]
            if expected_version is not None and current != expected_version:
                raise ValueError("Analysis changed. Refresh before retrying.")
            analysis["version"] = (current or 0) + 1
            db.execute("INSERT INTO analyses VALUES (?,?,?)", (analysis["id"], analysis["version"], json.dumps(analysis)))
        return analysis

    def list(self):
        with self.connect() as db:
            rows = db.execute("""SELECT a.payload FROM analyses a JOIN
                (SELECT id, MAX(version) v FROM analyses GROUP BY id) b
                ON a.id=b.id AND a.version=b.v ORDER BY a.rowid DESC LIMIT 100""").fetchall()
        return [json.loads(row[0]) for row in rows]

    def history(self, analysis_id):
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM analyses WHERE id=? ORDER BY version DESC", (analysis_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def incidents(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM incidents ORDER BY id")]

    def put_incident(self, incident, seed=False):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO incidents VALUES (?,?)" if seed else
                       "INSERT OR REPLACE INTO incidents VALUES (?,?)", (incident["id"], json.dumps(incident)))
        return incident

    def job(self, job_id):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise KeyError("Run not found")
        return json.loads(row[0])

    def active(self, analysis_id):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM jobs WHERE analysis_id=? AND status IN ('queued','running')", (analysis_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def put_job(self, job):
        with self.connect() as db:
            db.execute("INSERT INTO jobs VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,payload=excluded.payload",
                       (job["id"], job["analysis_id"], job["status"], json.dumps(job)))
        return job

    def recover_jobs(self):
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM jobs WHERE status IN ('queued','running')").fetchall()
            for row in rows:
                job = json.loads(row[0])
                job.update(status="interrupted", detail="Service restarted before completion. Inspect remote builds before running again.")
                db.execute("UPDATE jobs SET status=?,payload=? WHERE id=?", (job["status"], json.dumps(job), job["id"]))
