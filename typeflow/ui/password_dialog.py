from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel
from qfluentwidgets import LineEdit, PrimaryPushButton


class PasswordDialog(QDialog):
    def __init__(self, create_mode: bool, parent=None):
        super().__init__(parent=parent)
        self.create_mode = create_mode
        self.setWindowTitle("Set encryption password" if create_mode else "Unlock history")
        self.password = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Password"), 0, 0)
        self.input = LineEdit(self)
        self.input.setEchoMode(LineEdit.Password)
        layout.addWidget(self.input, 0, 1)

        self.confirm_input = None
        if self.create_mode:
            layout.addWidget(QLabel("Confirm"), 1, 0)
            self.confirm_input = LineEdit(self)
            self.confirm_input.setEchoMode(LineEdit.Password)
            layout.addWidget(self.confirm_input, 1, 1)

        self.ok_btn = PrimaryPushButton("OK", self)
        self.ok_btn.clicked.connect(self.accept)
        layout.addWidget(self.ok_btn, 2, 1)

    def accept(self) -> None:
        pwd = self.input.text()
        if not pwd:
            return
        if self.create_mode and self.confirm_input:
            if pwd != self.confirm_input.text():
                return
        self.password = pwd
        super().accept()

    def get_password(self) -> str:
        return self.password
