from pathlib import Path

APP_NAME = "TypeFlow"
DATA_DIR = Path.home() / ".typeflow"
DB_PATH = DATA_DIR / "typeflow.db"

# Typing session heuristics
IDLE_THRESHOLD_SECONDS = 4.0  # pause that ends a typing streak
ENGAGE_THRESHOLD_SECONDS = 2.0  # time in active typing before counting as engaged
STREAK_MIN_DURATION = 5.0
HISTORY_MERGE_WINDOW_SECONDS = 1.5  # merge keystrokes into one record when close in time

# Crypto parameters
KDF_ITERATIONS = 200_000
KEY_LENGTH = 32
SALT_BYTES = 16

# UI defaults
HISTORY_PAGE_SIZE = 200
MAX_QUEUED_EVENTS = 5000
DEFAULT_THEME = "dark"  # dark | light | system
DEFAULT_FONT_SIZE = 14.0
