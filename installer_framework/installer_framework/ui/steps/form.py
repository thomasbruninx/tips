"""Generic form step for custom fields."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QCheckBox, QComboBox, QLabel

from installer_framework.config.conditions import evaluate_condition
from installer_framework.config.validation import validate_field_value
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicCheckboxRow, ClassicGroupBox
from installer_framework.ui.widgets.validated_text_input import ValidatedTextInput


class FormStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.controls: dict[str, Any] = {}

        group = ClassicGroupBox(theme=self.theme, title=self.step_config.title)
        group.content_layout.addWidget(self.description_label(height=40))

        for field in self.step_config.fields:
            if not evaluate_condition(field.show_if, self.ctx.state):
                continue

            if field.type in {"text", "password"}:
                control = ValidatedTextInput(field=field)
                self.controls[field.id] = control
                group.content_layout.addWidget(control)
            elif field.type == "checkbox":
                row = ClassicCheckboxRow(theme=self.theme, text=field.label, active=bool(field.default))
                self.controls[field.id] = row.checkbox
                group.content_layout.addWidget(row)
            elif field.type == "select":
                label = QLabel(field.label)
                label.setStyleSheet(f"color: {self.theme.text_primary};")
                combo = QComboBox()
                combo.addItems(field.choices)
                if field.default:
                    combo.setCurrentText(str(field.default))
                combo.setStyleSheet(
                    f"QComboBox {{ background-color: {self.theme.panel_bg}; color: {self.theme.text_primary}; border: 1px solid {self.theme.border_dark}; padding: 2px 4px; }}"
                )
                self.controls[field.id] = combo
                group.content_layout.addWidget(label)
                group.content_layout.addWidget(combo)

        self.main_layout.addWidget(group)

    def apply_state(self) -> None:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            value = self.ctx.state.answers.get(field.id, field.default)
            if isinstance(control, ValidatedTextInput):
                control.set_value(value)
            elif isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            else:
                if value is not None:
                    control.setCurrentText(str(value))

    def get_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            if isinstance(control, ValidatedTextInput):
                data[field.id] = control.value
            elif isinstance(control, QCheckBox):
                data[field.id] = bool(control.isChecked())
            else:
                data[field.id] = control.currentText()
        return data

    def validate(self) -> tuple[bool, str | None]:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if isinstance(control, ValidatedTextInput):
                ok, message = control.validate()
                if not ok:
                    return False, f"{field.label}: {message}"
                ok, message = validate_field_value(field, control.value)
                if not ok:
                    return False, f"{field.label}: {message}"
            elif isinstance(control, QCheckBox):
                ok, message = validate_field_value(field, bool(control.isChecked()))
                if not ok:
                    return False, f"{field.label}: {message}"
            elif control is not None:
                ok, message = validate_field_value(field, control.currentText())
                if not ok:
                    return False, f"{field.label}: {message}"
        return True, None
