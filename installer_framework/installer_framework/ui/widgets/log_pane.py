"""Toggleable log pane widget for install output."""

from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.classic import ClassicButton, ClassicPanel


_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())


class LogPane(ClassicPanel):
    def __init__(self, **kwargs) -> None:
        self.theme: UITheme = get_active_theme() or _DEFAULT_THEME
        super().__init__(
            theme=self.theme,
            orientation="vertical",
            spacing=dp(6),
            padding=(dp(6), dp(6)),
            fill_color=self.theme.panel_bg,
            border=True,
            **kwargs,
        )
        self.visible = False

        self.toggle_btn = ClassicButton(
            theme=self.theme,
            text="Details >>",
            size_hint_y=None,
            height=dp(self.theme.config.metrics.button_height),
        )
        self.toggle_btn.bind(on_release=lambda *_: self.toggle())

        self.scroll = ScrollView(size_hint_y=None, height=0, disabled=True, opacity=0)
        self.output = TextInput(readonly=True, multiline=True, size_hint_y=None, height=dp(210))
        self.output.background_normal = ""
        self.output.background_active = ""
        self.output.background_color = self.theme.panel_bg
        self.output.foreground_color = self.theme.text_primary
        if self.theme.font_name:
            self.output.font_name = self.theme.font_name

        self.scroll.add_widget(self.output)

        self.add_widget(self.toggle_btn)
        self.add_widget(self.scroll)

    def toggle(self) -> None:
        self.visible = not self.visible
        self.scroll.opacity = 1 if self.visible else 0
        self.scroll.disabled = not self.visible
        self.scroll.height = dp(210) if self.visible else 0
        self.toggle_btn.text = "<< Details" if self.visible else "Details >>"

    def append(self, line: str) -> None:
        self.output.text += f"{line}\n"
        self.output.cursor = (0, len(self.output._lines))

    def get_text(self) -> str:
        return self.output.text
