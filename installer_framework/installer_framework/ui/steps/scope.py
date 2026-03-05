"""Install scope selection step."""

from __future__ import annotations

from kivy.uix.checkbox import CheckBox

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicCheckboxRow, ClassicGroupBox


class ScopeStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.user_row = ClassicCheckboxRow(theme=self.theme, text="Install for current user", active=True)
        self.system_row = ClassicCheckboxRow(theme=self.theme, text="Install for all users (requires administrator)")

        self.user_row.checkbox.group = "scope"
        self.system_row.checkbox.group = "scope"

        group = ClassicGroupBox(theme=self.theme, title="Install Scope")
        group.content.add_widget(self.description_label(height=40))
        group.content.add_widget(self.user_row)
        group.content.add_widget(self.system_row)

        self.add_widget(group)

    def apply_state(self) -> None:
        scope = self.ctx.state.install_scope
        self.system_row.checkbox.active = scope == "system"
        self.user_row.checkbox.active = scope != "system"

    def get_data(self) -> dict:
        scope = "system" if self.system_row.checkbox.active else "user"
        return {"install_scope": scope}

    def validate(self) -> tuple[bool, str | None]:
        if not self.user_row.checkbox.active and not self.system_row.checkbox.active:
            return False, "Please select an install scope"
        return True, None
