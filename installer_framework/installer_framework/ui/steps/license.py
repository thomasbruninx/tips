"""License agreement step."""

from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicButton, ClassicCheckboxRow, ClassicGroupBox


class LicenseStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agree_row = ClassicCheckboxRow(theme=self.theme, text="I agree to the license terms", active=False)

        license_text = self._load_license_text()
        scroll = ScrollView(size_hint=(1, 1))
        self.license_view = TextInput(text=license_text, readonly=True, multiline=True)
        self.license_view.background_normal = ""
        self.license_view.background_active = ""
        self.license_view.background_color = self.theme.panel_bg
        self.license_view.foreground_color = self.theme.text_primary
        if self.theme.font_name:
            self.license_view.font_name = self.theme.font_name
        scroll.add_widget(self.license_view)

        group = ClassicGroupBox(theme=self.theme, title="License Agreement")
        group.content.add_widget(scroll)

        button_row = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(self.theme.config.metrics.button_height))
        button_row.add_widget(BoxLayout())
        disagree = ClassicButton(theme=self.theme, text="Disagree", size_hint_x=None, width=dp(100))
        disagree.bind(on_release=lambda *_: self.wizard.cancel_install("License not accepted"))
        button_row.add_widget(disagree)

        self.add_widget(group)
        self.add_widget(self.agree_row)
        self.add_widget(button_row)

    def _load_license_text(self) -> str:
        candidate = self.step_config.license_path or ""
        if not candidate:
            return "No license configured."

        path = Path(candidate)
        if not path.is_absolute():
            path = (self.ctx.config.source_root / candidate).resolve()

        if not path.exists():
            return f"License file not found: {path}"
        return path.read_text(encoding="utf-8", errors="replace")

    def get_data(self) -> dict:
        return {"license_agree": self.agree_row.checkbox.active}

    def apply_state(self) -> None:
        self.agree_row.checkbox.active = bool(self.ctx.state.answers.get("license_agree", False))

    def validate(self) -> tuple[bool, str | None]:
        if not self.agree_row.checkbox.active:
            return False, "You must accept the license to continue."
        return True, None
