"""Base widget for all wizard steps."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from installer_framework.config.models import StepConfig, ThemeConfig
from installer_framework.engine.context import InstallerContext
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.theme import ThemeWidgetFactory, build_widget_factory


class StepWidget(QWidget):
    """Common behavior for step views."""

    def __init__(self, step_config: StepConfig, ctx: InstallerContext, wizard, **kwargs) -> None:
        super().__init__(**kwargs)
        theme = getattr(wizard, "theme", None) or get_active_theme()
        self.step_config = step_config
        self.ctx = ctx
        self.wizard = wizard
        self.theme: UITheme = theme or UITheme(config=ThemeConfig(), source_root=Path.cwd())
        self.widget_factory: ThemeWidgetFactory = getattr(wizard, "widget_factory", None) or build_widget_factory(
            self.theme
        )

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)

    def _font(self, size: int, bold: bool = False) -> QFont:
        font = QFont()
        if self.theme.font_name:
            font.setFamily(self.theme.font_name)
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def title_label(self, text: str | None = None) -> QLabel:
        label = QLabel(text or self.step_config.title)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setFont(self._font(self.theme.title_size, bold=True))
        label.setStyleSheet(f"color: {self.theme.text_primary};")
        label.setFixedHeight(30)
        return label

    def resolved_body_description(self) -> str:
        if self.step_config.body_description is not None:
            return self.step_config.body_description
        return self.step_config.description

    def description_label(self, text: str | None = None, height: int = 30) -> QLabel:
        resolved = self.resolved_body_description() if text is None else text
        label = QLabel(resolved)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        label.setFont(self._font(self.theme.base_size))
        label.setStyleSheet(f"color: {self.theme.text_primary};")
        if not resolved.strip():
            label.setVisible(False)
            label.setFixedHeight(0)
            return label
        label.setFixedHeight(height)
        return label

    def on_show(self) -> None:
        """Called when the step is displayed."""

    def get_data(self) -> dict[str, Any]:
        """Collect values from UI controls."""
        return {}

    def validate(self) -> tuple[bool, str | None]:
        """Return (is_valid, optional_error_message)."""
        return True, None

    def apply_state(self) -> None:
        """Populate controls from state."""
