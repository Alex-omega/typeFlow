import multiprocessing as mp
import shutil
import sys
from typing import List, Optional

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog

from . import config
from .database import open_database
from .encryption import CryptoManager
from .keyboard_hook import KeyboardMonitor
from .models import HistoryEntry
from .stats import TypingStatsEngine
from .service import run_service
from .ui.main_window import MainWindow
from .ui.password_dialog import PasswordDialog
from .ui.tray import TrayIcon


class TypeFlowController:
    def __init__(self):
        self.db = open_database()
        self.crypto: Optional[CryptoManager] = None
        self.engine = TypingStatsEngine(self.db, crypto=None)
        self.capturing = False
        self.theme = self.db.get_meta("ui_theme") or config.DEFAULT_THEME
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

    def ensure_password(self, parent) -> bool:
        record = self.db.load_password_record()
        if not record:
            dialog = PasswordDialog(create_mode=True, parent=parent)
            if dialog.exec_() != QDialog.Accepted:
                return False
            mgr = CryptoManager(dialog.get_password())
            self.crypto = mgr
            self.engine.set_crypto(mgr)
            self.db.save_password_record(mgr.password_record())
            return True

        dialog = PasswordDialog(create_mode=False, parent=parent)
        if dialog.exec_() == QDialog.Accepted:
            if not self.unlock(dialog.get_password()):
                QMessageBox.warning(parent, config.APP_NAME, "Password incorrect; history remains locked.")
        return True

    def unlock(self, password: str) -> bool:
        record = self.db.load_password_record()
        if not record:
            return False
        mgr = CryptoManager.verify_password(password, record)
        if not mgr:
            return False
        self.crypto = mgr
        self.engine.set_crypto(mgr)
        if self.capture_flag is None and self.service_process is None:
            # if service not started, start it with the unlocked password
            self.start_service(password)
        return True

    def fetch_history(self, offset: int, limit: int) -> List[HistoryEntry]:
        entries = self.db.secure_history(offset, limit)
        if not self.crypto:
            return []
        return [HistoryEntry(ts=e.ts, text=self.crypto.decrypt_text(e.text)) for e in entries]

    def snapshot(self):
        return self.engine.snapshot()

    def daily(self):
        return self.db.daily_snapshots()

    def start_capture(self):
        if self.capturing:
            return
        self.monitor.start()
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
        self.service_process = mp.Process(
            target=run_service,
            args=(self.stop_event, self.capture_flag, password),
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
    controller = TypeFlowController()
    first_run = controller.db.load_password_record() is None
    if not controller.ensure_password(None):
        return
    # ensure monitor service is running
    if controller.crypto:
        controller.start_service(password=controller.crypto.password if hasattr(controller.crypto, "password") else "")
    window = MainWindow(controller)
    tray = TrayIcon(controller, window)
    tray.show()
    if first_run:
        window.show()
    else:
        # show transient toast in the center bottom
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.success(
            title="TypeFlow 已成功启动！",
            content="后台正在运行，可在托盘打开主界面。",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=3000,
            parent=window,
        )
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
