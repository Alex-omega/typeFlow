import threading
import time
from datetime import datetime
from typing import Optional

from . import config
from .database import Database
from .encryption import CryptoManager
from .models import KeyFrequency, SessionStat, StatsSnapshot


class TypingStatsEngine:
    def __init__(self, db: Database, crypto: Optional[CryptoManager] = None):
        self.db = db
        self.crypto = crypto
        self._lock = threading.Lock()
        self._current_session_start: Optional[float] = None
        self._last_event_ts: Optional[float] = None
        self._keys_this_session = 0
        self._engaged_start: Optional[float] = None
        self._history_buffer: str = ""
        self._history_last_ts: Optional[float] = None

    def _finalize_session(self, end_ts: float) -> None:
        if self._current_session_start is None:
            return
        engaged_seconds = 0.0
        if self._engaged_start:
            engaged_seconds = max(0.0, end_ts - self._engaged_start)
        session = SessionStat(
            start_ts=self._current_session_start,
            end_ts=end_ts,
            keystrokes=self._keys_this_session,
            engaged_seconds=engaged_seconds,
        )
        self._flush_history(force=True)
        self.db.add_session(session)
        day = datetime.fromtimestamp(self._current_session_start).strftime("%Y-%m-%d")
        streak = 1 if (end_ts - self._current_session_start) >= config.STREAK_MIN_DURATION else 0
        self.db.update_daily_summary(
            day=day,
            keystrokes=self._keys_this_session,
            active_seconds=engaged_seconds,
            streaks=streak,
        )
        self._current_session_start = None
        self._last_event_ts = None
        self._keys_this_session = 0
        self._engaged_start = None

    def handle_event(self, key_label: str, text: str, ts: Optional[float] = None) -> None:
        timestamp = ts or time.time()
        with self._lock:
            if self._last_event_ts and (timestamp - self._last_event_ts) > config.IDLE_THRESHOLD_SECONDS:
                self._finalize_session(self._last_event_ts)
            if self._current_session_start is None:
                self._current_session_start = timestamp
                self._keys_this_session = 0
                self._engaged_start = None

            self._keys_this_session += 1
            self.db.increment_key_usage(key_label)
            self._append_history(text=text, ts=timestamp)

            elapsed = timestamp - self._current_session_start
            if self._engaged_start is None and elapsed >= config.ENGAGE_THRESHOLD_SECONDS:
                self._engaged_start = timestamp - config.ENGAGE_THRESHOLD_SECONDS

            self._last_event_ts = timestamp

    def tick_idle(self) -> None:
        with self._lock:
            if self._last_event_ts and (time.time() - self._last_event_ts) > config.IDLE_THRESHOLD_SECONDS:
                self._flush_history(force=True)
                self._finalize_session(self._last_event_ts)

    def snapshot(self) -> StatsSnapshot:
        key_usage = self.db.key_usage_all()
        typing_keys = [k for k in key_usage if self._is_letter(k.key)]
        total_keys = sum(k.count for k in typing_keys)
        engaged_seconds = self.db.total_engaged_seconds()
        avg_kpm = 0.0
        if engaged_seconds > 0:
            avg_kpm = (total_keys / engaged_seconds) * 60.0
        top_candidates = [k for k in key_usage if (self._is_letter(k.key) or self._is_space(k.key))]
        top_keys = sorted(top_candidates, key=lambda x: x.count, reverse=True)[:12]
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.db.daily_summary(today)
        streaks_today = daily.streaks if daily else 0
        active_today = daily.active_seconds if daily else 0.0
        return StatsSnapshot(
            total_keys=total_keys,
            avg_kpm=avg_kpm,
            top_keys=top_keys,
            streaks_today=streaks_today,
            active_seconds_today=active_today,
        )

    def set_crypto(self, crypto: Optional[CryptoManager]) -> None:
        with self._lock:
            self.crypto = crypto

    def _is_letter(self, label: str) -> bool:
        return len(label) == 1 and label.isalpha()

    def _is_space(self, label: str) -> bool:
        return label.lower() == "space" or label == " "

    def _append_history(self, text: str, ts: float) -> None:
        if not text:
            return
        # Always record history; encrypt when crypto is available, otherwise store raw text.
        if self.crypto:
            if self._history_buffer and self._history_last_ts:
                if (ts - self._history_last_ts) > config.HISTORY_MERGE_WINDOW_SECONDS:
                    self._flush_history()
            self._history_buffer += text
            self._history_last_ts = ts
            if text.endswith("\n"):
                self._flush_history()
        else:
            self.db.add_secure_event(ts, text)

    def _flush_history(self, force: bool = False) -> None:
        if not self._history_buffer or not self.crypto:
            self._history_buffer = ""
            self._history_last_ts = None
            return
        ts = self._history_last_ts or time.time()
        encrypted = self.crypto.encrypt_text(self._history_buffer)
        self.db.add_secure_event(ts, encrypted)
        self._history_buffer = ""
        self._history_last_ts = None
