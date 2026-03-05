"""Base widget for all wizard steps."""

from __future__ import annotations

from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from installer_framework.config.models import StepConfig
from installer_framework.engine.context import InstallerContext
from installer_framework.ui.theme import UITheme, get_active_theme


class StepWidget(BoxLayout):
    """Common behavior for step views."""

    def __init__(self, step_config: StepConfig, ctx: InstallerContext, wizard, **kwargs) -> None:
        theme = getattr(wizard, "theme", None) or get_active_theme()
        spacing = dp(8)
        padding = dp(8)
        super().__init__(orientation="vertical", spacing=spacing, padding=padding, **kwargs)
        self.step_config = step_config
        self.ctx = ctx
        self.wizard = wizard
        self.theme: UITheme | None = theme

    def title_label(self, text: str | None = None) -> Label:
        label = Label(
            text=text or self.step_config.title,
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=self.theme.text_primary if self.theme else (1, 1, 1, 1),
            font_size=f"{self.theme.base_size}sp" if self.theme else "14sp",
        )
        label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        if self.theme and self.theme.font_name:
            label.font_name = self.theme.font_name
        return label

    def description_label(self, text: str | None = None, height: int = 30) -> Label:
        label = Label(
            text=text or self.step_config.description,
            size_hint_y=None,
            height=dp(height),
            halign="left",
            valign="top",
            color=self.theme.text_primary if self.theme else (1, 1, 1, 1),
            font_size=f"{self.theme.base_size}sp" if self.theme else "14sp",
        )
        label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        if self.theme and self.theme.font_name:
            label.font_name = self.theme.font_name
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
