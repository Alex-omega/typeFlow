import sqlite3
import threading
import time
from pathlib import Path
from typing import Iterable, List, Optional

from . import config
from .encryption import PasswordRecord
from .models import DailySummary, HistoryEntry, KeyFrequency, SessionStat


class Database:
    def __init__(self, db_path: Path = config.DB_PATH):
        self.db_path = db_path
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._setup()

    def _setup(self) -> None:
        with self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS key_usage (
                    key TEXT PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_ts REAL NOT NULL,
                    end_ts REAL NOT NULL,
                    keystrokes INTEGER NOT NULL,
                    engaged_seconds REAL NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS secure_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_summary (
                    day TEXT PRIMARY KEY,
                    keystrokes INTEGER NOT NULL DEFAULT 0,
                    active_seconds REAL NOT NULL DEFAULT 0,
                    streaks INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    # Meta helpers
    def get_meta(self, key: str) -> Optional[str]:
        cur = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def increment_typing_total(self, amount: int = 1) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO meta(key, value) VALUES ('typing_total', ?)
                ON CONFLICT(key) DO UPDATE SET value = CAST(meta.value AS INTEGER) + ?
                """,
                (amount, amount),
            )

    def typing_total(self) -> int:
        cur = self._conn.execute("SELECT value FROM meta WHERE key = 'typing_total'")
        row = cur.fetchone()
        return int(row["value"]) if row and row["value"] is not None else 0

    def save_password_record(self, record: PasswordRecord) -> None:
        self.set_meta("password_salt_b64", record.salt_b64)
        self.set_meta("password_verifier_b64", record.verifier_b64)

    def load_password_record(self) -> Optional[PasswordRecord]:
        salt = self.get_meta("password_salt_b64")
        verifier = self.get_meta("password_verifier_b64")
        if not salt or not verifier:
            return None
        return PasswordRecord(salt_b64=salt, verifier_b64=verifier)

    # Event storage
    def increment_key_usage(self, key_label: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO key_usage(key, count) VALUES (?, 1)
                ON CONFLICT(key) DO UPDATE SET count = count + 1
                """,
                (key_label,),
            )

    def add_secure_event(self, ts: float, payload: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO secure_events(ts, payload) VALUES (?, ?)",
                (ts, payload),
            )

    def add_session(self, session: SessionStat) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO sessions(start_ts, end_ts, keystrokes, engaged_seconds, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session.start_ts,
                    session.end_ts,
                    session.keystrokes,
                    session.engaged_seconds,
                    time.time(),
                ),
            )

    def update_daily_summary(self, day: str, keystrokes: int, active_seconds: float, streaks: int) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO daily_summary(day, keystrokes, active_seconds, streaks)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(day) DO UPDATE SET
                    keystrokes = daily_summary.keystrokes + excluded.keystrokes,
                    active_seconds = daily_summary.active_seconds + excluded.active_seconds,
                    streaks = daily_summary.streaks + excluded.streaks
                """,
                (day, keystrokes, active_seconds, streaks),
            )

    # Queries
    def top_keys(self, limit: int = 10) -> List[KeyFrequency]:
        cur = self._conn.execute(
            "SELECT key, count FROM key_usage ORDER BY count DESC LIMIT ?",
            (limit,),
        )
        return [KeyFrequency(row["key"], row["count"]) for row in cur.fetchall()]

    def key_usage_all(self) -> List[KeyFrequency]:
        cur = self._conn.execute("SELECT key, count FROM key_usage")
        return [KeyFrequency(row["key"], row["count"]) for row in cur.fetchall()]

    def latest_sessions(self, limit: int = 20) -> List[SessionStat]:
        cur = self._conn.execute(
            "SELECT start_ts, end_ts, keystrokes, engaged_seconds FROM sessions ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [
            SessionStat(
                start_ts=row["start_ts"],
                end_ts=row["end_ts"],
                keystrokes=row["keystrokes"],
                engaged_seconds=row["engaged_seconds"],
            )
            for row in cur.fetchall()
        ]

    def daily_snapshots(self, limit: int = 14) -> List[DailySummary]:
        cur = self._conn.execute(
            "SELECT day, keystrokes, active_seconds, streaks FROM daily_summary ORDER BY day DESC LIMIT ?",
            (limit,),
        )
        return [
            DailySummary(
                day=row["day"],
                keystrokes=row["keystrokes"],
                active_seconds=row["active_seconds"],
                streaks=row["streaks"],
            )
            for row in cur.fetchall()
        ]

    def daily_summary(self, day: str) -> Optional[DailySummary]:
        cur = self._conn.execute(
            "SELECT day, keystrokes, active_seconds, streaks FROM daily_summary WHERE day = ?",
            (day,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return DailySummary(
            day=row["day"],
            keystrokes=row["keystrokes"],
            active_seconds=row["active_seconds"],
            streaks=row["streaks"],
        )

    def secure_history(self, offset: int, limit: int) -> List[HistoryEntry]:
        cur = self._conn.execute(
            "SELECT ts, payload FROM secure_events ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [HistoryEntry(ts=row["ts"], text=row["payload"]) for row in cur.fetchall()]

    def total_keystrokes(self) -> int:
        cur = self._conn.execute("SELECT SUM(count) as total FROM key_usage")
        row = cur.fetchone()
        return row["total"] or 0

    def total_engaged_seconds(self) -> float:
        cur = self._conn.execute("SELECT SUM(engaged_seconds) as total FROM sessions")
        row = cur.fetchone()
        return row["total"] or 0.0

    def events_count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) as c FROM secure_events")
        row = cur.fetchone()
        return row["c"] or 0

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def open_database() -> Database:
    return Database()
