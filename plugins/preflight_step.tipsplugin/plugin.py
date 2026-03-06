"""Preflight checklist custom step plugin."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel

from installer_framework.ui.step_base import StepWidget


class PreflightStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.answer_key = str(self.step_config.params.get("answer_key") or f"{self.step_config.id}_acknowledged")
        self.required_ack = bool(self.step_config.params.get("required_ack", True))
        ack_label = str(self.step_config.params.get("ack_label") or "I confirm all pre-install checks are complete.")

        group = self.widget_factory.create_group_box(title=self.step_config.title)
        group.content_layout.addWidget(self.description_label(height=50))

        checklist = self.step_config.params.get("checklist") or []
        for item in checklist:
            label = QLabel(f"- {item}")
            label.setWordWrap(True)
            label.setStyleSheet(f"color: {self.theme.text_primary};")
            group.content_layout.addWidget(label)

        row = self.widget_factory.create_checkbox_row(text=ack_label, active=False)
        self.ack_checkbox = row.checkbox
        group.content_layout.addWidget(row)
        group.content_layout.addStretch(1)

        self.main_layout.addWidget(group)

    def apply_state(self) -> None:
        current = bool(self.ctx.state.answers.get(self.answer_key, False))
        self.ack_checkbox.setChecked(current)

    def get_data(self) -> dict:
        return {self.answer_key: bool(self.ack_checkbox.isChecked())}

    def validate(self) -> tuple[bool, str | None]:
        if self.required_ack and not self.ack_checkbox.isChecked():
            return False, "Please acknowledge the pre-install checklist to continue."
        return True, None


def register() -> dict:
    return {"step_class": PreflightStep}
