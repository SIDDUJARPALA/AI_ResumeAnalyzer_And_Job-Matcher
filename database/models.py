import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


@contextmanager
def _connect(database_path):
    connection = sqlite3.connect(database_path)
    try:
        connection.row_factory = sqlite3.Row
        with connection:
            yield connection
    finally:
        connection.close()


def init_db(database_path):
    with _connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                file_name TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )


def save_analysis(database_path, analysis_id, file_name, result):
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result["created_at"] = created_at
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO analyses (id, created_at, file_name, result_json)
            VALUES (?, ?, ?, ?)
            """,
            (analysis_id, created_at, file_name, json.dumps(result, ensure_ascii=True)),
        )


def get_analysis(database_path, analysis_id):
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT result_json FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
    return json.loads(row["result_json"]) if row else None


def get_recent_analyses(database_path, limit=12):
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, file_name, result_json
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    recent = []
    for row in rows:
        result = json.loads(row["result_json"])
        job = result.get("job") or {}
        recent.append(
            {
                "id": row["id"],
                "title": job.get("title") or row["file_name"],
                "created_at": row["created_at"],
            }
        )
    return recent


def update_analysis(database_path, analysis_id, result):
    with _connect(database_path) as connection:
        connection.execute(
            "UPDATE analyses SET result_json = ? WHERE id = ?",
            (json.dumps(result, ensure_ascii=True), analysis_id),
        )


def delete_analysis(database_path, analysis_id):
    with _connect(database_path) as connection:
        connection.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
