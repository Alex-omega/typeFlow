import threading
import time
from typing import Optional

from pynput import keyboard

from . import config
from .stats import TypingStatsEngine


SPECIAL_NAMES = {
    keyboard.Key.enter: "Enter",
    keyboard.Key.space: "Space",
    keyboard.Key.backspace: "Backspace",
    keyboard.Key.tab: "Tab",
    keyboard.Key.shift: "Shift",
    keyboard.Key.shift_r: "Shift",
    keyboard.Key.ctrl: "Ctrl",
    keyboard.Key.ctrl_r: "Ctrl",
    keyboard.Key.alt: "Alt",
    keyboard.Key.alt_r: "Alt",
}


class KeyboardMonitor:
    def __init__(self, engine: TypingStatsEngine):
        self.engine = engine
        self.listener: Optional[keyboard.Listener] = None
        self._idle_thread = threading.Thread(target=self._idle_watchdog, daemon=True)
        self._running = False

    def start(self) -> None:
        if self.listener:
            return
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
        self._running = True
        if not self._idle_thread.is_alive():
            self._idle_thread.start()

    def stop(self) -> None:
        self._running = False
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_press(self, key) -> None:
        key_label = self._key_label(key)
        text = key.char if hasattr(key, "char") and key.char else key_label
        self.engine.handle_event(key_label=key_label, text=text)

    def _key_label(self, key) -> str:
        if key in SPECIAL_NAMES:
            return SPECIAL_NAMES[key]
        if hasattr(key, "char") and key.char:
            return key.char
        return str(key)

    def _idle_watchdog(self) -> None:
        while True:
            if self._running:
                self.engine.tick_idle()
            time.sleep(config.IDLE_THRESHOLD_SECONDS / 2)
