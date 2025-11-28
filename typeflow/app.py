import importlib
import importlib.util
import multiprocessing as mp
import os
import secrets
import shutil
import sys
from pathlib import Path
from typing import List, Optional

# Normalize sys.path for PyInstaller/onefile and direct script execution
HERE = Path(__file__).resolve()
PKG_DIR = HERE.parent
PROJ_ROOT = PKG_DIR.parent
for p in [PKG_DIR, PROJ_ROOT]:
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    mp_root = str(Path(sys._MEIPASS))
    if mp_root not in sys.path:
        sys.path.insert(0, mp_root)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox


def _import(module: str, fallback: str = "", rel_file: str | None = None):
    """Import helper that tries package name, fallback, then file path."""
    try:
        return importlib.import_module(module)
    except ImportError:
        if fallback:
            try:
                return importlib.import_module(fallback)
            except ImportError:
                pass
        if rel_file:
            candidate = PKG_DIR / rel_file
            if candidate.exists():
                spec = importlib.util.spec_from_file_location(module, candidate)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    sys.modules[module] = mod
                    return mod
        raise


config = _import("typeflow.config", "config", "config.py")
open_database = _import("typeflow.database", "database", "database.py").open_database
CryptoManager = _import("typeflow.encryption", "encryption", "encryption.py").CryptoManager
HistoryEntry = _import("typeflow.models", "models", "models.py").HistoryEntry
TypingStatsEngine = _import("typeflow.stats", "stats", "stats.py").TypingStatsEngine
run_service = _import("typeflow.service", "service", "service.py").run_service
MainWindow = _import("typeflow.ui.main_window", "ui.main_window", "ui/main_window.py").MainWindow
TrayIcon = _import("typeflow.ui.tray", "ui.tray", "ui/tray.py").TrayIcon

LOCK_MAGIC = b"\x11\x84\x13\x10"
_lock_handle: Optional[int] = None
_lock_path = None


def acquire_single_instance() -> bool:
    """Use magic-number lock file to prevent multi-instance."""
    global _lock_handle, _lock_path
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _lock_path = config.DATA_DIR / "typeflow.lock"
    try:
        fd = os.open(str(_lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(fd, LOCK_MAGIC + str(os.getpid()).encode())
        _lock_handle = fd
        return True
    except FileExistsError:
        return False
    except Exception:
        return True  # fail-open to avoid blocking startup unexpectedly


def release_single_instance() -> None:
    global _lock_handle, _lock_path
    if _lock_handle is not None:
        try:
            os.close(_lock_handle)
        except Exception:
            pass
    if _lock_path and os.path.exists(_lock_path):
        try:
            os.remove(_lock_path)
        except Exception:
            pass


class TypeFlowController:
    def __init__(self):
        self.db = open_database()
        self.crypto: Optional[CryptoManager] = None
        self.engine = TypingStatsEngine(self.db, crypto=None)
        self.capturing = False
        self.theme = self.db.get_meta("ui_theme") or config.DEFAULT_THEME
        initial_record = self.db.load_password_record()
        self.first_run = initial_record is None
        font_size_meta = self.db.get_meta("ui_font_size")
        if font_size_meta:
            self.font_size = float(font_size_meta)
        else:
            # backward compatibility: support old font scale meta
            legacy_scale = self.db.get_meta("ui_font_scale")
            if legacy_scale:
                self.font_size = max(8.0, float(legacy_scale) * config.DEFAULT_FONT_SIZE)
            else:
                self.font_size = config.DEFAULT_FONT_SIZE
        self.service_process: Optional[mp.Process] = None
        self.stop_event: Optional[mp.Event] = None
        self.capture_flag: Optional[mp.Value] = None
        self._bootstrap_crypto(initial_record)

    def _bootstrap_crypto(self, record=None) -> None:
        if record is None:
            record = self.db.load_password_record()
        cached = self.db.get_meta("cached_password")
        if record and cached:
            mgr = CryptoManager.verify_password(cached, record)
            if mgr:
                self.crypto = mgr
                self.engine.set_crypto(mgr)
                return

    def unlock(self, password: str) -> bool:
        record = self.db.load_password_record()
        if not record:
            # 创建新的密码记录
            mgr = CryptoManager(password)
            self.db.save_password_record(mgr.password_record())
        else:
            mgr = CryptoManager.verify_password(password, record)
            if not mgr:
                return False
        self.crypto = mgr
        self.engine.set_crypto(mgr)
        self.db.set_meta("cached_password", password)
        # 重启后台服务以使用新的密码加密历史
        self.stop_service()
        self.start_service(password)
        return True

    def fetch_history(self, offset: int, limit: int) -> List[HistoryEntry]:
        entries = self.db.secure_history(offset, limit)
        if not self.crypto:
            return entries
        return [HistoryEntry(ts=e.ts, text=self.crypto.decrypt_text(e.text)) for e in entries]

    def snapshot(self):
        return self.engine.snapshot()

    def daily(self):
        return self.db.daily_snapshots()

    def start_capture(self):
        if self.capturing:
            return
        if self.capture_flag:
            self.capture_flag.value = True
        self.capturing = True

    def pause_capture(self):
        if not self.capturing:
            return
        if self.capture_flag:
            self.capture_flag.value = False
        self.capturing = False

    def uninstall(self) -> bool:
        """Clear all stored data (db + password) and return to fresh state."""
        self.pause_capture()
        self.crypto = None
        self.engine.set_crypto(None)
        ok = True
        try:
            self.db.close()
        except Exception:
            ok = False
        try:
            if config.DATA_DIR.exists():
                shutil.rmtree(config.DATA_DIR)
        except Exception:
            ok = False
        self.db = open_database()
        self.engine = TypingStatsEngine(self.db, crypto=None)
        self.capturing = False
        return ok

    def set_theme(self, theme: str) -> None:
        self.theme = theme
        self.db.set_meta("ui_theme", theme)

    def set_font_size(self, size: float) -> None:
        self.font_size = size
        self.db.set_meta("ui_font_size", str(size))

    def settings_snapshot(self):
        return {
            "theme": self.theme,
            "font_size": self.font_size,
            "capturing": self.capturing,
        }

    def start_service(self, password: str) -> None:
        if self.service_process and self.service_process.is_alive():
            return
        mp.set_start_method("spawn", force=True)
        self.stop_event = mp.Event()
        self.capture_flag = mp.Value("b", True)
        self.capturing = True
        pw = password or self.db.get_meta("cached_password") or ""
        self.service_process = mp.Process(
            target=run_service,
            args=(self.stop_event, self.capture_flag, pw),
            daemon=True,
        )
        self.service_process.start()

    def stop_service(self) -> None:
        if self.stop_event:
            self.stop_event.set()
        if self.service_process:
            self.service_process.join(timeout=5)
        self.service_process = None
        self.stop_event = None
        self.capture_flag = None
        self.capturing = False

    def shutdown(self):
        self.pause_capture()
        self.engine.tick_idle()
        self.db.close()


def main():
    app = QApplication(sys.argv)
    if not acquire_single_instance():
        QMessageBox.information(None, "TypeFlow", "Typeflow已在运行中！")
        return
    controller = TypeFlowController()
    first_run = controller.first_run
    if controller.crypto:
        controller.start_service(password=getattr(controller.crypto, "password", ""))
    else:
        controller.start_service(password="")
    window = MainWindow(controller)
    tray = TrayIcon(controller, window)
    tray.show()
    from qfluentwidgets import InfoBar, InfoBarPosition
    if first_run:
        window.show()
    else:
        InfoBar.success(
            title="TypeFlow 已成功启动！",
            content="后台正在运行，可在托盘打开主界面。",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=3000,
            parent=window,
        )
    code = app.exec_()
    controller.stop_service()
    release_single_instance()
    sys.exit(code)

if __name__ == "__main__":
    main()
