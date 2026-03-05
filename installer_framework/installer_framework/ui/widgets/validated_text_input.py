"""Field widget with built-in text/password validation helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from installer_framework.config.models import FieldConfig
from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme

_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())


class ValidatedTextInput(QWidget):
    def __init__(self, field: FieldConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme: UITheme = get_active_theme() or _DEFAULT_THEME
        self.field = field

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        self.label = QLabel(field.label)
        self.label.setStyleSheet(f"color: {self.theme.text_primary};")

        self.input = QLineEdit(str(field.default or ""))
        self.input.setEchoMode(QLineEdit.EchoMode.Password if field.type == "password" else QLineEdit.EchoMode.Normal)
        self.input.setPlaceholderText(field.placeholder or "")
        self.input.setStyleSheet(
            f"QLineEdit {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; padding: 2px 4px; }}"
        )

        self.error = QLabel("")
        self.error.setStyleSheet("color: #B00020;")
        self.error.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.error)

        self.setFixedHeight(76)

    @property
    def value(self) -> str:
        return self.input.text().strip()

    def set_value(self, value: Any) -> None:
        self.input.setText("" if value is None else str(value))

    def validate(self) -> tuple[bool, str | None]:
        text = self.value
        self.error.setText("")

        if self.field.required and not text:
            return self._fail("This field is required")

        if self.field.min_length is not None and len(text) < self.field.min_length:
            return self._fail(f"Minimum length: {self.field.min_length}")

        if self.field.max_length is not None and len(text) > self.field.max_length:
            return self._fail(f"Maximum length: {self.field.max_length}")

        if self.field.regex and text and not re.match(self.field.regex, text):
            return self._fail("Invalid format")

        if self.field.type == "password" and self.field.complexity and text:
            if not (re.search(r"[A-Z]", text) and re.search(r"[a-z]", text) and re.search(r"\d", text)):
                return self._fail("Password must contain upper/lowercase and digit")

        return True, None

    def _fail(self, message: str) -> tuple[bool, str]:
        self.error.setText(message)
        return False, message
