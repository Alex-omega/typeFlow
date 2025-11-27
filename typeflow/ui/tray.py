from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon
from qfluentwidgets import FluentIcon

from ..resources import asset_path


class TrayIcon(QSystemTrayIcon):
    def __init__(self, controller, window, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.window = window
        icon_file = asset_path("icon.ico")
        icon = QIcon(str(icon_file)) if icon_file.exists() else FluentIcon.EDIT.icon()
        self.setIcon(icon)
        self._build_menu()

    def _build_menu(self) -> None:
        menu = QMenu()
        open_action = QAction("Open TypeFlow", self)
        open_action.triggered.connect(self._open_window)
        menu.addAction(open_action)

        self.toggle_action = QAction("Pause capture", self)
        self.toggle_action.triggered.connect(self._toggle_capture)
        menu.addAction(self.toggle_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _open_window(self) -> None:
        self.window.showNormal()
        self.window.activateWindow()

    def _toggle_capture(self) -> None:
        if self.controller.capturing:
            self.controller.pause_capture()
            self.toggle_action.setText("Resume capture")
            self.showMessage("TypeFlow", "Keyboard capture paused.")
        else:
            self.controller.start_capture()
            self.toggle_action.setText("Pause capture")
            self.showMessage("TypeFlow", "Keyboard capture running.")

    def _quit(self) -> None:
        self.controller.shutdown()
        self.hide()
        self.window.close()
