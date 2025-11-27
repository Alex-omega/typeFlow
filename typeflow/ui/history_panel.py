from datetime import datetime
from typing import Callable, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, StrongBodyLabel

from .. import config
from ..models import HistoryEntry


class HistoryPage(QWidget):
    def __init__(
        self,
        unlock_handler: Callable[[str], bool],
        fetch_handler: Callable[[int, int], List[HistoryEntry]],
        parent=None,
    ):
        super().__init__(parent=parent)
        self.unlock_handler = unlock_handler
        self.fetch_handler = fetch_handler
        self.page = 0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        layout.addWidget(StrongBodyLabel("Unlock to view full typing history"))
        hint = BodyLabel(
            "History stays encrypted at rest. Enter your password to decrypt stored keystrokes. "
            "Stats remain visible without it."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        input_row = QHBoxLayout()
        self.password_input = LineEdit(self)
        self.password_input.setEchoMode(LineEdit.Password)
        self.password_input.setPlaceholderText("Encryption password")
        self.unlock_btn = PrimaryPushButton("Unlock", self)
        self.unlock_btn.clicked.connect(self._on_unlock)
        input_row.addWidget(self.password_input)
        input_row.addWidget(self.unlock_btn)
        layout.addLayout(input_row)

        self.refresh_btn = PrimaryPushButton("Refresh", self)
        self.refresh_btn.clicked.connect(self.reload)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignLeft)

        self.list_widget = QListWidget(self)
        layout.addWidget(self.list_widget, stretch=1)

    def _on_unlock(self) -> None:
        password = self.password_input.text()
        if not password:
            return
        ok = self.unlock_handler(password)
        if not ok:
            QMessageBox.warning(self, "TypeFlow", "Invalid password, please try again.")
            return
        self.reload()

    def reload(self) -> None:
        entries = self.fetch_handler(self.page * config.HISTORY_PAGE_SIZE, config.HISTORY_PAGE_SIZE)
        self._render(entries)

    def _render(self, entries: List[HistoryEntry]) -> None:
        self.list_widget.clear()
        for entry in entries:
            ts = datetime.fromtimestamp(entry.ts).strftime("%Y-%m-%d %H:%M:%S")
            item = QListWidgetItem(f"[{ts}] {entry.text}")
            self.list_widget.addItem(item)
