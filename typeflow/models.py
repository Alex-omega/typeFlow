from dataclasses import dataclass
from typing import List


@dataclass
class KeyEvent:
    ts: float
    key_label: str
    text: str


@dataclass
class SessionStat:
    start_ts: float
    end_ts: float
    keystrokes: int
    engaged_seconds: float


@dataclass
class KeyFrequency:
    key: str
    count: int


@dataclass
class DailySummary:
    day: str
    keystrokes: int
    active_seconds: float
    streaks: int


@dataclass
class HistoryEntry:
    ts: float
    text: str


@dataclass
class StatsSnapshot:
    total_keys: int
    avg_kpm: float
    top_keys: List[KeyFrequency]
    streaks_today: int
    active_seconds_today: float
