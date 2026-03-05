"""Generic form step for custom fields."""

from __future__ import annotations

from typing import Any

from kivy.metrics import dp
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner

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
        group.content.add_widget(self.description_label(height=40))

        for field in self.step_config.fields:
            if not evaluate_condition(field.show_if, self.ctx.state):
                continue

            if field.type in {"text", "password"}:
                control = ValidatedTextInput(field=field)
                self.controls[field.id] = control
                group.content.add_widget(control)
            elif field.type == "checkbox":
                row = ClassicCheckboxRow(theme=self.theme, text=field.label, active=bool(field.default))
                self.controls[field.id] = row.checkbox
                group.content.add_widget(row)
            elif field.type == "select":
                group.content.add_widget(self.description_label(text=field.label, height=22))
                spinner = Spinner(
                    text=str(field.default or (field.choices[0] if field.choices else "")),
                    values=field.choices,
                    size_hint_y=None,
                    height=dp(30),
                )
                spinner.background_normal = ""
                spinner.background_down = ""
                spinner.background_color = self.theme.panel_bg
                spinner.color = self.theme.text_primary
                if self.theme.font_name:
                    spinner.font_name = self.theme.font_name
                self.controls[field.id] = spinner
                group.content.add_widget(spinner)

        self.add_widget(group)

    def apply_state(self) -> None:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            value = self.ctx.state.answers.get(field.id, field.default)
            if isinstance(control, ValidatedTextInput):
                control.set_value(value)
            elif isinstance(control, CheckBox):
                control.active = bool(value)
            else:
                if value is not None:
                    control.text = str(value)

    def get_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            if isinstance(control, ValidatedTextInput):
                data[field.id] = control.value
            elif isinstance(control, CheckBox):
                data[field.id] = bool(control.active)
            else:
                data[field.id] = control.text
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
            elif isinstance(control, CheckBox):
                ok, message = validate_field_value(field, bool(control.active))
                if not ok:
                    return False, f"{field.label}: {message}"
            elif control is not None:
                ok, message = validate_field_value(field, control.text)
                if not ok:
                    return False, f"{field.label}: {message}"
        return True, None
