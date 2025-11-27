import sys
from typing import List, Optional

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog

from . import config
from .database import open_database
from .encryption import CryptoManager
from .keyboard_hook import KeyboardMonitor
from .models import HistoryEntry
from .stats import TypingStatsEngine
from .ui.main_window import MainWindow
from .ui.password_dialog import PasswordDialog
from .ui.tray import TrayIcon


class TypeFlowController:
    def __init__(self):
        self.db = open_database()
        self.crypto: Optional[CryptoManager] = None
        self.engine = TypingStatsEngine(self.db, crypto=None)
        self.monitor = KeyboardMonitor(self.engine)
        self.capturing = False

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
        self.monitor.stop()
        self.capturing = False

    def shutdown(self):
        self.pause_capture()
        self.engine.tick_idle()
        self.db.close()


def main():
    app = QApplication(sys.argv)
    controller = TypeFlowController()
    if not controller.ensure_password(None):
        return
    window = MainWindow(controller)
    tray = TrayIcon(controller, window)
    tray.show()
    window.show()
    controller.start_capture()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
