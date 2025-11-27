from datetime import datetime
from typing import List

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, CardWidget, StrongBodyLabel, TitleLabel

from ..models import DailySummary, KeyFrequency, StatsSnapshot


class SummaryCard(CardWidget):
    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        layout.addWidget(BodyLabel(title))
        value_label = TitleLabel(value)
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(value_label)
        layout.addStretch(1)
        self.value_label = value_label

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DashboardPage")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.total_card = SummaryCard("Total keystrokes", "0")
        self.speed_card = SummaryCard("Average KPM", "0")
        self.streak_card = SummaryCard("Streaks today", "0")
        self.active_card = SummaryCard("Active time today", "0s")

        cards = QWidget()
        card_layout = QGridLayout(cards)
        card_layout.setSpacing(10)
        card_layout.addWidget(self.total_card, 0, 0)
        card_layout.addWidget(self.speed_card, 0, 1)
        card_layout.addWidget(self.streak_card, 1, 0)
        card_layout.addWidget(self.active_card, 1, 1)
        layout.addWidget(cards)

        self.chart = pg.PlotWidget()
        self.chart.showGrid(x=True, y=True, alpha=0.15)
        self.chart.setBackground("transparent")
        self.chart.getAxis("left").setPen(pg.mkPen(color=(180, 180, 180)))
        self.chart.getAxis("bottom").setPen(pg.mkPen(color=(180, 180, 180)))
        layout.addWidget(self.chart, stretch=2)

        self.top_keys_table = QTableWidget(0, 2)
        self.top_keys_table.setHorizontalHeaderLabels(["Key", "Count"])
        self.top_keys_table.horizontalHeader().setStretchLastSection(True)
        self.top_keys_table.verticalHeader().setVisible(False)
        self.top_keys_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(StrongBodyLabel("Top keys"))
        layout.addWidget(self.top_keys_table, stretch=1)

    def set_data(self, snapshot: StatsSnapshot, daily: List[DailySummary]) -> None:
        self.total_card.set_value(f"{snapshot.total_keys:,}")
        self.speed_card.set_value(f"{snapshot.avg_kpm:.1f} kpm")
        self.streak_card.set_value(str(snapshot.streaks_today))
        active_minutes = snapshot.active_seconds_today / 60
        self.active_card.set_value(f"{active_minutes:.1f} min")

        self._update_chart(daily)
        self._update_top_keys(snapshot.top_keys)

    def _update_chart(self, daily: List[DailySummary]) -> None:
        if not daily:
            self.chart.clear()
            return
        xs = list(range(len(daily)))[::-1]
        ys = [d.keystrokes for d in reversed(daily)]
        labels = [datetime.strptime(d.day, "%Y-%m-%d").strftime("%m-%d") for d in reversed(daily)]
        self.chart.clear()
        bar_graph = pg.BarGraphItem(x=xs, height=ys, width=0.8, brush=pg.mkBrush("#5DADE2"))
        self.chart.addItem(bar_graph)
        axis = self.chart.getAxis("bottom")
        axis.setTicks([list(zip(xs, labels))])

    def _update_top_keys(self, keys: List[KeyFrequency]) -> None:
        self.top_keys_table.setRowCount(len(keys))
        for row, item in enumerate(keys):
            self.top_keys_table.setItem(row, 0, QTableWidgetItem(item.key))
            self.top_keys_table.setItem(row, 1, QTableWidgetItem(str(item.count)))
