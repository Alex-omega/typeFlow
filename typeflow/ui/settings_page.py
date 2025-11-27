from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)
from qfluentwidgets import StrongBodyLabel, BodyLabel


class SettingsPage(QWidget):
    def __init__(
        self,
        initial_state: dict,
        on_capture_toggle,
        on_theme_change,
        on_font_scale_change,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.setObjectName("SettingsPage")
        self.on_capture_toggle = on_capture_toggle
        self.on_theme_change = on_theme_change
        self.on_font_scale_change = on_font_scale_change
        self._build_ui(initial_state)

    def _build_ui(self, state: dict) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        layout.addWidget(StrongBodyLabel("捕获与外观"))
        layout.addWidget(BodyLabel("在此暂停/启用记录，并调整主题与字号。"))

        self.capture_checkbox = QCheckBox("启用记录", self)
        self.capture_checkbox.setChecked(state.get("capturing", False))
        self.capture_checkbox.stateChanged.connect(self._capture_changed)
        layout.addWidget(self.capture_checkbox)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("主题模式"))
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItems(["dark", "light", "system"])
        current_theme = state.get("theme", "dark")
        idx = self.theme_combo.findText(current_theme)
        if idx != -1:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentTextChanged.connect(self.on_theme_change)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        layout.addLayout(theme_row)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("字号缩放"))
        self.font_slider = QSlider(Qt.Horizontal, self)
        self.font_slider.setMinimum(80)
        self.font_slider.setMaximum(140)
        self.font_slider.setSingleStep(5)
        scale = float(state.get("font_scale", 1.0))
        self.font_slider.setValue(int(scale * 100))
        self.font_slider.valueChanged.connect(self._font_scale_changed)
        font_row.addWidget(self.font_slider)
        self.font_label = QLabel(f"{scale:.2f}x")
        font_row.addWidget(self.font_label)
        layout.addLayout(font_row)

        layout.addStretch(1)

    def _capture_changed(self, state):
        enabled = state == Qt.Checked
        self.on_capture_toggle(enabled)

    def _font_scale_changed(self, value: int):
        scale = value / 100.0
        self.font_label.setText(f"{scale:.2f}x")
        self.on_font_scale_change(scale)

    def update_capture_state(self, enabled: bool) -> None:
        self.capture_checkbox.blockSignals(True)
        self.capture_checkbox.setChecked(enabled)
        self.capture_checkbox.blockSignals(False)
