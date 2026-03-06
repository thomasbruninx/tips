"""Welcome step."""

from __future__ import annotations

from PyQt6.QtWidgets import QRadioButton

from installer_framework.ui.step_base import StepWidget


class WelcomeStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.upgrade_group = self.widget_factory.create_group_box(title="Upgrade options")
        self.upgrade_group.setVisible(False)

        self.radio_in_place = QRadioButton("Upgrade in place")
        self.radio_change_dir = QRadioButton("Change installation directory")
        self.radio_uninstall = QRadioButton("Uninstall first (placeholder)")

        for radio in (self.radio_in_place, self.radio_change_dir, self.radio_uninstall):
            radio.setStyleSheet(f"QRadioButton {{ color: {self.theme.text_primary}; }}")
            self.upgrade_group.content_layout.addWidget(radio)

        self.main_layout.addWidget(self.description_label(height=72))
        self.main_layout.addWidget(self.upgrade_group)
        self.main_layout.addStretch(1)

    def apply_state(self) -> None:
        mode = self.ctx.state.answers.get("upgrade_mode", "upgrade_in_place")
        self.radio_in_place.setChecked(mode == "upgrade_in_place")
        self.radio_change_dir.setChecked(mode == "change_directory")
        self.radio_uninstall.setChecked(mode == "uninstall_first")

    def on_show(self) -> None:
        detected = self.ctx.state.detected_upgrade
        if detected:
            self.upgrade_group.setVisible(True)
            self.upgrade_group.setTitle(
                f"Existing installation detected: Version {detected.get('version')} at {detected.get('install_dir')}"
            )
        else:
            self.upgrade_group.setVisible(False)

    def get_data(self) -> dict:
        if not self.upgrade_group.isVisible():
            return {}
        if self.radio_change_dir.isChecked():
            mode = "change_directory"
        elif self.radio_uninstall.isChecked():
            mode = "uninstall_first"
        else:
            mode = "upgrade_in_place"
        return {"upgrade_mode": mode}
