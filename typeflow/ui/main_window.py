from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
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


class MainWindow(FluentWindow):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        setTheme(Theme.DARK)
        self.dashboard_page = DashboardPage(self)
        self.history_page = HistoryPage(
            unlock_handler=self._unlock_history,
            fetch_handler=self.controller.fetch_history,
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
