from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (
    FluentIcon,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    NavigationItemPosition,
    Theme,
    setTheme,
)

from .. import config
from ..models import DailySummary, StatsSnapshot
from ..resources import asset_path
from .dashboard import DashboardPage
from .history_panel import HistoryPage
from .settings_page import SettingsPage


class MainWindow(FluentWindow):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        self.apply_theme(controller.theme)
        self.apply_font_scale(controller.font_scale)
        self.dashboard_page = DashboardPage(self)
        self.history_page = HistoryPage(
            unlock_handler=self._unlock_history,
            fetch_handler=self.controller.fetch_history,
            parent=self,
        )
        self.settings_page = SettingsPage(
            initial_state=self.controller.settings_snapshot(),
            on_capture_toggle=self._on_capture_toggle,
            on_theme_change=self._on_theme_change,
            on_font_scale_change=self._on_font_scale_change,
            parent=self,
        )
        self._init_navigation()
        self._init_timer()
        self.setWindowTitle(config.APP_NAME)
        icon_file = asset_path("icon_256.png")
        if not icon_file.exists():
            icon_file = asset_path("icon.ico")
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1000, 720)
        self.refresh()

    def _init_navigation(self) -> None:
        self.addSubInterface(
            self.dashboard_page,
            FluentIcon.HOME,
            "Dashboard",
            NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.history_page,
            FluentIcon.HISTORY,
            "History",
            NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.settings_page,
            FluentIcon.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )

    def _init_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

    def refresh(self) -> None:
        snapshot: StatsSnapshot = self.controller.snapshot()
        daily: list[DailySummary] = self.controller.daily()
        self.dashboard_page.set_data(snapshot, daily)

    def _unlock_history(self, password: str) -> bool:
        ok = self.controller.unlock(password)
        if ok:
            InfoBar.success(
                title="Unlocked",
                content="History decrypted for this session.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        else:
            InfoBar.error(
                title="Wrong password",
                content="Unable to decrypt history.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        return ok

    def _on_capture_toggle(self, enabled: bool) -> None:
        if enabled:
            self.controller.start_capture()
        else:
            self.controller.pause_capture()
        self.settings_page.update_capture_state(enabled)

    def _on_theme_change(self, theme: str) -> None:
        self.controller.set_theme(theme)
        self.apply_theme(theme)

    def _on_font_scale_change(self, scale: float) -> None:
        self.controller.set_font_scale(scale)
        self.apply_font_scale(scale)

    def apply_theme(self, theme: str) -> None:
        if theme == "light":
            setTheme(Theme.LIGHT)
        elif theme == "system":
            setTheme(Theme.AUTO)
        else:
            setTheme(Theme.DARK)

    def apply_font_scale(self, scale: float) -> None:
        app = QApplication.instance()
        if not app:
            return
        font = app.font()
        base_size = font.pointSizeF() or 11.0
        font.setPointSizeF(max(8.0, base_size * scale))
        app.setFont(font)
