"""Options step: checkboxes, selects, and feature multi-select."""

from __future__ import annotations

from typing import Any

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner

from installer_framework.config.conditions import evaluate_condition
from installer_framework.config.validation import validate_field_value
from installer_framework.ui.step_base import StepWidget
from installer_framework.ui.widgets.classic import ClassicCheckboxRow, ClassicGroupBox
from installer_framework.ui.widgets.feature_list import FeatureListWidget


class OptionsStep(StepWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.controls: dict[str, Any] = {}
        self.feature_list: FeatureListWidget | None = None

        group = ClassicGroupBox(theme=self.theme, title="Options")
        group.content.add_widget(self.description_label(height=40))

        for field in self.step_config.fields:
            if not evaluate_condition(field.show_if, self.ctx.state):
                continue
            if field.type == "checkbox":
                row = ClassicCheckboxRow(theme=self.theme, text=field.label, active=bool(field.default))
                self.controls[field.id] = row.checkbox
                group.content.add_widget(row)
            elif field.type == "select":
                group.content.add_widget(self.description_label(text=field.label, height=24))
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
            elif field.type == "multiselect":
                group.content.add_widget(self.description_label(text=field.label, height=24))
                features = self.ctx.config.features or []
                self.feature_list = FeatureListWidget(features=features, selected=self.ctx.state.selected_features, size_hint=(1, 1))
                self.controls[field.id] = self.feature_list
                group.content.add_widget(self.feature_list)

        self.add_widget(group)

    def apply_state(self) -> None:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            current = self.ctx.state.answers.get(field.id, field.default)
            if field.type == "checkbox":
                control.active = bool(current)
            elif field.type == "select" and current is not None:
                control.text = str(current)

    def get_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            if field.type == "checkbox":
                data[field.id] = bool(control.active)
            elif field.type == "select":
                data[field.id] = control.text
            elif field.type == "multiselect" and self.feature_list:
                selected = self.feature_list.get_selected()
                data[field.id] = selected
                data["selected_features"] = selected
        return data

    def validate(self) -> tuple[bool, str | None]:
        for field in self.step_config.fields:
            control = self.controls.get(field.id)
            if control is None:
                continue
            if field.type == "checkbox":
                value = bool(control.active)
            elif field.type == "select":
                value = control.text
            elif field.type == "multiselect" and self.feature_list:
                value = self.feature_list.get_selected()
            else:
                continue
            ok, message = validate_field_value(field, value)
            if not ok:
                return False, f"{field.label}: {message}"
        return True, None
