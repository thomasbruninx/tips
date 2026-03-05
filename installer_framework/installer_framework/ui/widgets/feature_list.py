"""Multi-select feature list widget with search filter."""

from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from installer_framework.config.models import FeatureConfig
from installer_framework.config.models import ThemeConfig
from installer_framework.ui.theme import UITheme, get_active_theme
from installer_framework.ui.widgets.classic import ClassicPanel


_DEFAULT_THEME = UITheme(config=ThemeConfig(), source_root=Path.cwd())


class FeatureListWidget(ClassicPanel):
    def __init__(self, features: list[FeatureConfig], selected: list[str] | None = None, **kwargs) -> None:
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
        self.features = features
        self.selected = set(selected or [])
        self.rows: list[tuple[FeatureConfig, BoxLayout, CheckBox]] = []

        self.search = TextInput(hint_text="Search features...", multiline=False, size_hint_y=None, height=dp(30))
        self.search.background_normal = ""
        self.search.background_active = ""
        self.search.background_color = self.theme.panel_bg
        self.search.foreground_color = self.theme.text_primary
        self.search.bind(text=lambda *_: self._apply_filter())

        self.scroll = ScrollView()
        self.container = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self.container.bind(minimum_height=lambda instance, value: setattr(instance, "height", value))
        self.scroll.add_widget(self.container)

        if self.theme.font_name:
            self.search.font_name = self.theme.font_name

        self.add_widget(self.search)
        self.add_widget(self.scroll)

        self._build_rows()

    def _build_rows(self) -> None:
        self.container.clear_widgets()
        self.rows.clear()
        for feature in self.features:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(6))
            checkbox = CheckBox(active=feature.id in self.selected or feature.default, size_hint_x=None, width=dp(34))
            label = Label(text=feature.label, color=self.theme.text_primary, halign="left", valign="middle")
            label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            if self.theme.font_name:
                label.font_name = self.theme.font_name
            row.add_widget(checkbox)
            row.add_widget(label)
            self.container.add_widget(row)
            self.rows.append((feature, row, checkbox))

    def _apply_filter(self) -> None:
        needle = self.search.text.strip().lower()
        for feature, row, _ in self.rows:
            visible = not needle or needle in feature.label.lower() or needle in feature.description.lower()
            row.height = dp(30) if visible else 0
            row.opacity = 1 if visible else 0
            row.disabled = not visible

    def get_selected(self) -> list[str]:
        result: list[str] = []
        for feature, _, checkbox in self.rows:
            if checkbox.active:
                result.append(feature.id)
        return result
