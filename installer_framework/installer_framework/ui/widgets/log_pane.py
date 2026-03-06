"""Toggleable log pane widget for install output."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.theme import build_widget_factory

_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())


class LogPane(QWidget):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme: UITheme = get_active_theme() or _DEFAULT_THEME
        self.widget_factory = build_widget_factory(self.theme)
        self.visible = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.toggle_btn = self.widget_factory.create_button("Details >>")
        self.toggle_btn.clicked.connect(self.toggle)
        self.toggle_btn.setFixedHeight(self.theme.config.metrics.button_height)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(180)
        self.output.setVisible(False)
        self.output.setStyleSheet(
            f"QTextEdit {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; }}"
        )

        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.output)

    def toggle(self) -> None:
        self.visible = not self.visible
        self.output.setVisible(self.visible)
        self.toggle_btn.setText("<< Details" if self.visible else "Details >>")

    def append(self, line: str) -> None:
        self.output.append(line)

    def get_text(self) -> str:
        return self.output.toPlainText()
