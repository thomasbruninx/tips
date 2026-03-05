"""Welcome step."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicGroupBox


class WelcomeStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.upgrade_group = ClassicGroupBox(theme=self.theme, title="Upgrade options", size_hint_y=None, height=0, opacity=0)

        self.radio_in_place = CheckBox(group="upgrade_mode", active=True, size_hint_x=None, width=dp(30))
        self.radio_change_dir = CheckBox(group="upgrade_mode", size_hint_x=None, width=dp(30))
        self.radio_uninstall = CheckBox(group="upgrade_mode", size_hint_x=None, width=dp(30))

        self.add_widget(self.description_label(height=72))
        self.add_widget(self.upgrade_group)

        for checkbox, text in (
            (self.radio_in_place, "Upgrade in place"),
            (self.radio_change_dir, "Change installation directory"),
            (self.radio_uninstall, "Uninstall first (placeholder)"),
        ):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(6))
            row.add_widget(checkbox)
            label = Label(text=text, color=self.theme.text_primary, halign="left", valign="middle")
            label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            if self.theme.font_name:
                label.font_name = self.theme.font_name
            row.add_widget(label)
            self.upgrade_group.content.add_widget(row)

    def apply_state(self) -> None:
        mode = self.ctx.state.answers.get("upgrade_mode", "upgrade_in_place")
        self.radio_in_place.active = mode == "upgrade_in_place"
        self.radio_change_dir.active = mode == "change_directory"
        self.radio_uninstall.active = mode == "uninstall_first"

    def on_show(self) -> None:
        detected = self.ctx.state.detected_upgrade
        if detected:
            self.upgrade_group.height = dp(130)
            self.upgrade_group.opacity = 1
            self.upgrade_group.title_label.text = (
                f"[b]Existing installation detected:[/b] Version {detected.get('version')} at {detected.get('install_dir')}"
            )
        else:
            self.upgrade_group.height = 0
            self.upgrade_group.opacity = 0

    def get_data(self) -> dict:
        if self.upgrade_group.opacity == 0:
            return {}
        if self.radio_change_dir.active:
            mode = "change_directory"
        elif self.radio_uninstall.active:
            mode = "uninstall_first"
        else:
            mode = "upgrade_in_place"
        return {"upgrade_mode": mode}
