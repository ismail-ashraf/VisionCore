
import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

from vision_core.core.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = Path(db_path)

    def initialize(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")

            connection.execute("""
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    throughput_fps REAL NOT NULL,
                    average_batch_latency_ms REAL NOT NULL,
                    average_wait_time_ms REAL NOT NULL,
                    queue_size INTEGER NOT NULL,
                    total_errors INTEGER NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS drift_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    camera_id TEXT NOT NULL,
                    brightness_psi REAL NOT NULL,
                    brightness_status TEXT NOT NULL,
                    contrast_psi REAL NOT NULL,
                    contrast_status TEXT NOT NULL,
                    sharpness_psi REAL NOT NULL,
                    sharpness_status TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    level TEXT NOT NULL,
                    event TEXT NOT NULL,
                    message TEXT NOT NULL,
                    camera_id TEXT
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp
                ON system_logs(timestamp)
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_logs_level
                ON system_logs(level)
            """)

    def save_system_log(
        self,
        level: str,
        event: str,
        message: str,
        camera_id: str | None = None,
    ):
        with self.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO system_logs (
                    timestamp,
                    level,
                    event,
                    message,
                    camera_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    level.upper(),
                    event,
                    message,
                    camera_id,
                ),
            )

    def get_system_logs(
        self,
        hours: int = 24,
        level: str | None = None,
        camera_id: str | None = None,
        search: str | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        cutoff = time.time() - (hours * 3600)

        query = """
            SELECT
                id,
                timestamp,
                level,
                event,
                message,
                camera_id
            FROM system_logs
            WHERE timestamp >= ?
        """

        params = [cutoff]

        if level:
            query += " AND level = ?"
            params.append(level.upper())

        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        if search:
            query += " AND (event LIKE ? OR message LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def get_performance_snapshots(
        self,
        hours: int = 24,
        limit: int = 1000,
    ) -> list[dict]:
        cutoff = time.time() - (hours * 3600)

        with self.get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    timestamp,
                    throughput_fps,
                    average_batch_latency_ms,
                    average_wait_time_ms,
                    queue_size,
                    total_errors
                FROM performance_snapshots
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()

        return [dict(row) for row in reversed(rows)]

    def get_drift_reports(
        self,
        hours: int = 24,
        camera_id: str | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        cutoff = time.time() - (hours * 3600)

        query = """
            SELECT
                timestamp,
                camera_id,
                brightness_psi,
                brightness_status,
                contrast_psi,
                contrast_status,
                sharpness_psi,
                sharpness_status
            FROM drift_reports
            WHERE timestamp >= ?
        """

        params = [cutoff]

        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in reversed(rows)]

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
