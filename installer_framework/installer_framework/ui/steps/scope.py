"""Install scope selection step."""

from __future__ import annotations

from PyQt6.QtWidgets import QRadioButton

from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicGroupBox


class ScopeStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.user_radio = QRadioButton("Install for current user")
        self.system_radio = QRadioButton("Install for all users (requires administrator)")

        self.user_radio.setStyleSheet(f"QRadioButton {{ color: {self.theme.text_primary}; }}")
        self.system_radio.setStyleSheet(f"QRadioButton {{ color: {self.theme.text_primary}; }}")

        group = ClassicGroupBox(theme=self.theme, title="Install Scope")
        group.content_layout.addWidget(self.description_label(height=40))
        group.content_layout.addWidget(self.user_radio)
        group.content_layout.addWidget(self.system_radio)

        self.main_layout.addWidget(group)
        self.main_layout.addStretch(1)

    def apply_state(self) -> None:
        scope = self.ctx.state.install_scope
        self.system_radio.setChecked(scope == "system")
        self.user_radio.setChecked(scope != "system")

    def get_data(self) -> dict:
        scope = "system" if self.system_radio.isChecked() else "user"
        return {"install_scope": scope}

    def validate(self) -> tuple[bool, str | None]:
        if not self.user_radio.isChecked() and not self.system_radio.isChecked():
            return False, "Please select an install scope"
        return True, None
