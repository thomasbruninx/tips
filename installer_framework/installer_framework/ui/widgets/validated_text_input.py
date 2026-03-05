"""Field widget with built-in text/password validation helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from installer_framework.config.models import FieldConfig
from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.classic import ClassicPanel


_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())


class ValidatedTextInput(ClassicPanel):
    def __init__(self, field: FieldConfig, **kwargs) -> None:
        self.theme: UITheme = get_active_theme() or _DEFAULT_THEME
        super().__init__(
            theme=self.theme,
            orientation="vertical",
            spacing=dp(3),
            size_hint_y=None,
            fill_color=self.theme.panel_bg,
            border=False,
            **kwargs,
        )
        self.field = field
        self.height = dp(76)

        self.label = Label(text=field.label, size_hint_y=None, height=dp(21), halign="left", valign="middle", color=self.theme.text_primary)
        self.label.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        self.input = TextInput(
            text=str(field.default or ""),
            multiline=False,
            password=field.type == "password",
            hint_text=field.placeholder or "",
            size_hint_y=None,
            height=dp(30),
        )
        self.input.background_normal = ""
        self.input.background_active = ""
        self.input.background_color = self.theme.panel_bg
        self.input.foreground_color = self.theme.text_primary
        self.input.cursor_color = self.theme.text_primary

        self.error = Label(text="", color=(0.75, 0.1, 0.1, 1), size_hint_y=None, height=dp(16), halign="left", valign="middle")
        self.error.bind(size=lambda instance, value: setattr(instance, "text_size", value))

        if self.theme.font_name:
            self.label.font_name = self.theme.font_name
            self.input.font_name = self.theme.font_name
            self.error.font_name = self.theme.font_name

        self.add_widget(self.label)
        self.add_widget(self.input)
        self.add_widget(self.error)

    @property
    def value(self) -> str:
        return self.input.text.strip()

    def set_value(self, value: Any) -> None:
        self.input.text = "" if value is None else str(value)

    def validate(self) -> tuple[bool, str | None]:
        text = self.value
        self.error.text = ""

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
        self.error.text = message
        return False, message
