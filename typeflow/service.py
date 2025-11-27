import multiprocessing as mp
import time
from typing import Optional

from . import config
from .database import open_database
from .encryption import CryptoManager
from .keyboard_hook import KeyboardMonitor
from .stats import TypingStatsEngine


def _load_crypto(password: str, db):
    record = db.load_password_record()
    if record:
        mgr = CryptoManager.verify_password(password, record)
        if mgr:
            return mgr
        # fallback: create new if verification fails (still allows running, but history decrypt may fail)
    mgr = CryptoManager(password)
    db.save_password_record(mgr.password_record())
    return mgr


def run_service(stop_event: mp.Event, capture_flag: mp.Value, password: str):
    """Background process entry: runs keyboard monitor and stats engine."""
    db = open_database()
    crypto = _load_crypto(password, db)
    engine = TypingStatsEngine(db, crypto=crypto)
    monitor = KeyboardMonitor(engine)

    try:
        while not stop_event.is_set():
            if capture_flag.value and not monitor.running:
                monitor.start()
            elif not capture_flag.value and monitor.running:
                monitor.stop()
            engine.tick_idle()
            time.sleep(config.IDLE_THRESHOLD_SECONDS / 2)
    finally:
        if monitor.running:
            monitor.stop()
        engine.tick_idle()
        db.close()
